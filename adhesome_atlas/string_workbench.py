"""Candidate selection, STRING API queries and session-scoped TSV topology."""
import hashlib
import io
import json
from pathlib import Path
import re
import time
import networkx as nx
import pandas as pd
import plotly.express as px
import streamlit as st
from data import SPECIES
from family_merges import atlas_group
from figure_exports import plotly_chart
from networks import mapping_export
from reconstruction import topology, network_matrices
from string_fetch import BASE, api_url, api_request, parameters, network_parameters, mapping_ids, tsv_rows
from vector_network import vector_network_html
from topological_clustering import clustering_panel

TAXA = {'Shae': 6185, 'Sjap': 6182, 'Sman': 6183}


def candidate_inventory(candidates, code, local_mapping):
    data = candidates[candidates.sequence_id.str.startswith(code + '__')].copy()
    data['query_family'] = data.get('reviewed_family', data.family).fillna('Unassigned')
    data['query_orthogroup'] = data.get('orthogroup', pd.Series('', index=data.index)).fillna('')
    data['query_group'] = data.query_orthogroup.map(atlas_group)
    lookup = {}
    for row in local_mapping.to_dict('records'):
        query = row['queryItem']
        if not query.startswith(code + '__'):
            query = code + '__' + query
        lookup.setdefault(query, set()).add(row['stringId'])
    data['query_id'] = data.sequence_id.map(lambda seq: next(iter(lookup[seq])) if len(lookup.get(seq, set())) == 1 else seq.split('__')[-1])
    data['query_basis'] = data.sequence_id.map(lambda seq: 'STRING query mapping' if len(lookup.get(seq, set())) == 1 else 'Atlas protein ID · API resolution required')
    return data.drop_duplicates(['sequence_id', 'query_family', 'query_orthogroup'])


def parse_network(text, species, score_scale=1):
    """Accept API or website exports; reject malformed, cross-species and directed data."""
    columns = ['node1_string_id', 'node2_string_id', 'node1', 'node2', 'combined_score']
    if not text.strip():
        return pd.DataFrame(columns=columns)
    data = pd.read_csv(io.StringIO(text), sep='\t', dtype=str).fillna('')
    data.columns = [name.lstrip('#') for name in data]
    if {'source_string_id', 'target_string_id'} <= set(data):
        raise ValueError('This is a directed regulatory network. Use a functional or physical STRING TSV for this undirected analysis.')
    if {'stringId_A', 'stringId_B', 'score'} <= set(data):
        rename = {'stringId_A': 'node1_string_id', 'stringId_B': 'node2_string_id', 'preferredName_A': 'node1', 'preferredName_B': 'node2', 'score': 'combined_score'}
        data = data.rename(columns=rename)
    if not {'node1_string_id', 'node2_string_id', 'combined_score'} <= set(data):
        raise ValueError('Expected STRING API stringId_A/stringId_B/score or website node1_string_id/node2_string_id/combined_score columns.')
    for endpoint, label in [('node1_string_id', 'node1'), ('node2_string_id', 'node2')]:
        if not data[endpoint].str.startswith(str(species) + '.').all():
            raise ValueError('TSV protein IDs do not match the selected species taxon ' + str(species) + '.')
        if label not in data:
            data[label] = data[endpoint].str.split('.', n=1).str[-1]
    if 'ncbiTaxonId' in data and not data.ncbiTaxonId.eq(str(species)).all():
        raise ValueError('TSV ncbiTaxonId does not match the selected species.')
    score = pd.to_numeric(data.combined_score, errors='coerce')
    if score.isna().any() or not score.between(0, score_scale).all():
        raise ValueError(f'Every combined score must be numeric and in the selected 0–{score_scale} scale.')
    data['combined_score'] = score / score_scale
    data = data[data.node1_string_id.ne(data.node2_string_id)].copy()
    data['pair'] = [tuple(sorted(pair)) for pair in zip(data.node1_string_id, data.node2_string_id)]
    return data.sort_values('combined_score', ascending=False, kind='stable').drop_duplicates('pair').drop(columns='pair').reset_index(drop=True)


def annotations_for_nodes(identifiers, candidates, local_mapping, plan, api_mapping, code):
    links = {}
    for record in local_mapping.to_dict('records'):
        seq = record['queryItem']
        if not seq.startswith(code + '__'):
            seq = code + '__' + seq
        links.setdefault(record['stringId'], set()).add(seq)
    for record in plan.to_dict('records'):
        query = record['query_id']
        sid = api_mapping.get(query, query if query.startswith(str(TAXA[code]) + '.') else '')
        if sid:
            links.setdefault(sid, set()).add(record['sequence_id'])
    source = candidates[candidates.sequence_id.str.startswith(code + '__')]
    known = set(source.sequence_id)
    rows = []
    for sid in sorted(set(identifiers)):
        # Exact node IDs are valid joins; labels alone are never used as identity mappings.
        direct = code + '__' + sid.split('.', 1)[-1]
        seqs = links.get(sid, set()).copy()
        if direct in known:
            seqs.add(direct)
        matched = source[source.sequence_id.isin(seqs)]
        join = lambda column: ' | '.join(sorted({str(v) for v in matched[column].dropna() if str(v)})) if column in matched else ''
        rows.append({'identifier': sid, 'sequence_id': ' | '.join(sorted(seqs)),
                     'Family': join('reviewed_family') or 'Unmapped', 'orthogroup': join('orthogroup'),
                     'candidate_annotation': join('candidate_annotation'), 'species': SPECIES[code],
                     'mapping_status': 'Many candidates share STRING representative' if len(seqs) > 1 else 'Mapped candidate' if seqs else 'Additional / unmapped STRING protein',
                     'layer': 'Unresolved'})
    return pd.DataFrame(rows, columns=['identifier', 'sequence_id', 'Family', 'orthogroup', 'candidate_annotation', 'species', 'mapping_status', 'layer'])


def analysis_panel(state, candidates, key='string_import_'):
    code = state['code']
    key += hashlib.sha256((code + state['raw'] + json.dumps(sorted(set(state.get('resolved', {}).values())))).encode()).hexdigest()[:12] + '_'
    taxon = TAXA[code]
    st.markdown('### Imported STRING network · topology and communities')
    st.caption('Source: ' + state['source'] + ' · ' + SPECIES[code] + ' · ' + state.get('network_type', 'User-declared network type') + '. This workspace is retained in the current session; original library exports remain unchanged.')
    a, b, c = st.columns(3)
    threshold = a.slider('Imported minimum combined score', 0.0, 1.0, 0.4, 0.01, key=key+'threshold')
    hide = b.checkbox('Hide unconnected imported nodes', value=False, key=key+'isolates')
    color_by = c.selectbox('Imported node colors', ['Family', 'orthogroup', 'community'], key=key+'color')
    edges = state['edges']
    ids = set(edges.node1_string_id) | set(edges.node2_string_id) | set(state.get('resolved', {}).values())
    nodes = annotations_for_nodes(ids, candidates, mapping_export(code), state['plan'], state.get('resolved', {}), code)
    labels = dict(zip(edges.node1_string_id, edges.node1)) | dict(zip(edges.node2_string_id, edges.node2))
    nodes['node'] = nodes.identifier.map(labels).fillna(nodes.identifier)
    families = st.multiselect('Filter imported families', sorted(nodes.Family.unique()), key=key+'families')
    if families:
        nodes = nodes[nodes.Family.isin(families)]
    focus = st.selectbox('Imported protein neighborhood', ['All proteins'] + sorted(nodes.identifier), key=key+'focus')
    edges = edges[edges.combined_score.ge(threshold) & edges.node1_string_id.isin(nodes.identifier) & edges.node2_string_id.isin(nodes.identifier)].copy()
    if focus != 'All proteins':
        neighborhood = {focus} | set(edges.loc[edges.node1_string_id.eq(focus), 'node2_string_id']) | set(edges.loc[edges.node2_string_id.eq(focus), 'node1_string_id'])
        nodes = nodes[nodes.identifier.isin(neighborhood)]
        edges = edges[edges.node1_string_id.isin(neighborhood) & edges.node2_string_id.isin(neighborhood)]
    if hide:
        connected = set(edges.node1_string_id) | set(edges.node2_string_id)
        nodes = nodes[nodes.identifier.isin(connected)]
    if nodes.empty:
        st.info('No nodes remain. Lower the score, show unconnected nodes, or fetch/import a network with resolved proteins.')
        return
    metrics, graph = topology(nodes, edges)
    for column, label, value in zip(st.columns(4), ['Proteins', 'Unique pairs', 'Components', 'Communities'], [len(metrics), graph.number_of_edges(), nx.number_connected_components(graph), metrics.community.nunique()]):
        column.metric(label, value)
    positions = nx.spring_layout(graph, seed=23, weight=None)
    colors = {category: px.colors.qualitative.Alphabet[i % 26] for i, category in enumerate(sorted(metrics[color_by].astype(str).unique()))}
    vector_nodes = [{'id': row.identifier, 'label': row.node, 'annotation': row.candidate_annotation,
        'x': float(positions[row.identifier][0]), 'y': float(positions[row.identifier][1]),
        'radius': 9 + row.degree ** .5 * 2, 'color': colors[str(getattr(row, color_by))], 'category': str(getattr(row, color_by)),
        'detail': {'Family': row.Family, 'Orthogroup': row.orthogroup, 'Candidate IDs': row.sequence_id,
                   'Mapping': row.mapping_status, 'Degree': int(row.degree), 'Betweenness': row.betweenness,
                   'Closeness': row.closeness, 'Clustering coefficient': row.clustering_coefficient, 'Community': int(row.community)}} for row in metrics.itertuples()]
    vector_edges = [{'source': row.node1_string_id, 'target': row.node2_string_id, 'width': 1 + 2 * row.combined_score} for row in edges.itertuples()]
    st.iframe(vector_network_html(vector_nodes, vector_edges, SPECIES[code] + ' · queried / imported STRING', label_mode='centered'), height=810)
    tabs = st.tabs(['Centrality & clusters', 'Interactions & mapping', 'Matrices', 'Query provenance'])
    with tabs[0]:
        st.caption('Unweighted undirected topology is recalculated after filtering. Betweenness is normalized; closeness uses the disconnected-graph correction. Communities use greedy modularity; local clustering and k-core describe neighborhood structure. STRING confidence filters edges and is not a path length.')
        st.dataframe(metrics, width='stretch', hide_index=True)
        st.download_button('Download imported centrality and clusters', metrics.to_csv(index=False), 'string_imported_topology.csv', key=key+'metrics')
        plotly_chart(px.scatter(metrics, x='closeness', y='betweenness', color=metrics.community.astype(str), size=metrics.degree.clip(lower=1), hover_name='node', hover_data=['degree', 'Family', 'orthogroup', 'clustering_coefficient'], title='Imported network · closeness and betweenness'), width='stretch', key=key+'centrality')
        summary = metrics.groupby('community').agg(proteins=('identifier', 'size'), mean_clustering=('clustering_coefficient', 'mean'), mean_degree=('degree', 'mean')).reset_index()
        st.dataframe(summary, width='stretch', hide_index=True)
        clustering_panel(graph, metrics, key + 'clustering', SPECIES[code] + ' · imported STRING')
    with tabs[1]:
        st.dataframe(edges, width='stretch', hide_index=True)
        st.download_button('Download filtered STRING interactions · TSV', edges.to_csv(sep='\t', index=False), 'string_imported_filtered.tsv', 'text/tab-separated-values', key=key+'edges')
        st.caption('Shared STRING representatives retain all mapped candidate IDs; no paralogue is chosen automatically. Additional neighbors remain visible with their mapping status.')
        st.dataframe(metrics[['identifier', 'node', 'sequence_id', 'Family', 'orthogroup', 'mapping_status']], width='stretch', hide_index=True)
    with tabs[2]:
        ordered = metrics.sort_values(['degree', 'identifier'], ascending=[False, True]).identifier.tolist()
        chosen = st.multiselect('Matrix proteins (maximum 60)', ordered, default=ordered[:min(20,len(ordered))], max_selections=60, key=key+'matrix')
        chosen = [identifier for identifier in chosen if identifier in graph]
        if chosen:
            distances, adjacency = network_matrices(graph, chosen)
            st.caption('Distances use paths through the entire displayed network; unreachable pairs are blank. Adjacency contains direct edges among the selected proteins.')
            plotly_chart(px.imshow(distances, aspect='auto', color_continuous_scale='YlGn', title='Shortest-path distance matrix'), width='stretch', key=key+'distance_plot')
            st.download_button('Download shortest-path matrix', distances.to_csv(), 'string_distance_matrix.csv', key=key+'distances')
            st.download_button('Download adjacency matrix', adjacency.to_csv(), 'string_adjacency_matrix.csv', key=key+'adjacency')
    with tabs[3]:
        st.json(state.get('provenance', {}))
        st.download_button('Download STRING query provenance', json.dumps(state.get('provenance', {}), indent=2), 'string_query_run.json', 'application/json', key=key+'provenance')
        st.download_button('Download original STRING response · TSV', state['raw'], 'string_network_original.tsv', 'text/tab-separated-values', key=key+'raw')
    if st.button('Clear imported STRING workspace', key=key+'clear'):
        st.session_state.pop('atlas_string_network', None)
        st.rerun()


def string_panel(candidates):
    st.markdown('### STRING query & TSV import')
    st.write('Choose catalogue families or orthogroups, resolve their proteins in STRING 12.5, and import the returned associations for interactive topology analysis.')
    code = st.selectbox('STRING query species', list(SPECIES), format_func=SPECIES.get, key='string_query_species')
    inventory = candidate_inventory(candidates, code, mapping_export(code))
    classifications = st.multiselect('Query candidate classification', sorted(inventory.audit_classification.dropna().unique()), default=[name for name in ['Supported','Provisional'] if name in set(inventory.audit_classification)], key='string_query_classification')
    inventory = inventory[inventory.audit_classification.isin(classifications)]
    selection = st.radio('Select STRING query proteins by', ['Protein families', 'Orthogroups'], horizontal=True, key='string_query_selection')
    if selection == 'Protein families':
        selected = st.multiselect('Protein families for STRING', sorted(inventory.query_family.unique()), key='string_query_families')
        plan = inventory[inventory.query_family.isin(selected)].copy()
    else:
        selected = st.multiselect('Orthogroups for STRING', sorted(set(inventory.query_group)-{''}), key='string_query_groups')
        plan = inventory[inventory.query_group.isin(selected)].copy()
    if len(plan) and st.checkbox('Refine the selected candidate list', key='string_query_refine'):
        proteins = st.multiselect('Candidate proteins for this query', sorted(plan.sequence_id.unique()), default=sorted(plan.sequence_id.unique()), key='string_query_proteins')
        plan = plan[plan.sequence_id.isin(proteins)]
    identifiers = sorted(set(plan.query_id))
    st.caption(f'{plan.sequence_id.nunique()} candidate proteins → {len(identifiers)} unique query IDs · taxon {TAXA[code]}. Families and orthogroups select their protein members; STRING is queried with protein IDs.')
    cols = [name for name in ['sequence_id', 'candidate_annotation', 'query_family', 'audit_classification', 'query_orthogroup', 'query_id', 'query_basis'] if name in plan]
    with st.expander('Selected candidates and STRING query mapping', expanded=bool(identifiers)):
        st.dataframe(plan[cols], width='stretch', hide_index=True)
    a, b, c = st.columns(3)
    score = a.slider('STRING required score (0–1000)', 0, 1000, 400, 10, key='string_query_score')
    extra = b.number_input('Additional STRING neighbors', min_value=0, max_value=100, value=0, key='string_query_extra')
    network_type = c.selectbox('STRING network type', ['functional', 'physical'], key='string_query_type')
    if identifiers:
        config = {'species': TAXA[code], 'identifiers': identifiers, 'score': score, 'add_nodes': int(extra), 'network_type': network_type,
                  'candidate_selection': plan[cols].to_dict('records'), 'string_version': '12.5'}
        signature = hashlib.sha256(json.dumps({'species': code, 'ids': identifiers}, sort_keys=True).encode()).hexdigest()
        map_params = parameters(identifiers, TAXA[code], echo_query=1)
        with st.expander('Standardized STRING GET URLs and WSL script'):
            st.code(api_url('get_string_ids', map_params), language='text')
            if len(api_url('get_string_ids', map_params)) <= 1800:
                st.link_button('Open STRING identifier mapping TSV', api_url('get_string_ids', map_params))
            st.download_button('Download STRING query configuration', json.dumps(config, indent=2), 'string_query.json', 'application/json', key='string_query_config')
            script = Path(__file__).with_name('string_fetch.py')
            st.download_button('Download STRING query script', script.read_bytes(), script.name, 'text/x-python', key='string_query_script')
            st.code('python3 string_fetch.py string_query.json --output STRING_results --fetch', language='bash')
            st.caption('Small queries use URL-encoded GET parameters. Long lists use POST. The script maps identifiers first, waits at least one second between API calls, and saves mapping, network TSV and provenance for upload below.')
        if st.button('1 · Resolve selected proteins in STRING', key='string_query_resolve'):
            try:
                with st.spinner('Resolving protein IDs in STRING 12.5…'):
                    raw, log = api_request('get_string_ids', map_params)
                    resolved, unresolved = mapping_ids(raw, identifiers, TAXA[code])
                st.session_state['atlas_string_mapping'] = {'signature': signature, 'raw': raw, 'resolved': resolved, 'unresolved': unresolved, 'log': log}
            except Exception as error:
                st.error('STRING mapping failed: ' + str(error))
        mapping = st.session_state.get('atlas_string_mapping')
        if mapping and mapping['signature'] == signature:
            st.success(f'{len(mapping["resolved"])} query IDs resolved; {len(mapping["unresolved"])} unresolved.')
            with st.expander('Resolved STRING protein mapping', expanded=True):
                st.dataframe(pd.DataFrame(tsv_rows(mapping['raw'], ['queryItem', 'stringId'])), width='stretch', hide_index=True)
            if mapping['unresolved']:
                st.write('Unresolved: ' + ', '.join(mapping['unresolved']))
            st.download_button('Download resolved STRING mapping · TSV', mapping['raw'], 'string_mapping.tsv', 'text/tab-separated-values', key='string_mapping_download')
            if mapping['resolved']:
                params = network_parameters(sorted(set(mapping['resolved'].values())), TAXA[code], score, extra, network_type)
                with st.expander('Resolved network URLs'):
                    for label, output in [('Network TSV', 'tsv'), ('Vector SVG', 'svg'), ('High-resolution PNG', 'highres_image')]:
                        url = api_url('network', params, output)
                        st.code(url, language='text')
                        if len(url) <= 1800:
                            st.link_button('Open STRING ' + label, url)
                if st.button('2 · Fetch STRING network and analyze', key='string_query_fetch'):
                    try:
                        # STRING asks clients to leave a second between calls.
                        time.sleep(1)
                        with st.spinner('Fetching the STRING association TSV…'):
                            raw, log = api_request('network', params)
                            edges = parse_network(raw, TAXA[code])
                        st.session_state['atlas_string_network'] = {'code': code, 'source': 'STRING 12.5 API', 'network_type': network_type,
                            'edges': edges, 'raw': raw, 'resolved': mapping['resolved'], 'plan': plan,
                            'provenance': {'config': config, 'mapping_request': mapping['log'], 'network_request': log, 'unresolved': mapping['unresolved']}}
                    except Exception as error:
                        st.error('STRING network fetch failed: ' + str(error))
    else:
        st.info('Select one or more families or orthogroups to create a STRING query. Existing TSVs can also be imported below.')
    with st.expander('Import a STRING TSV from your computer', expanded=not identifiers):
        uploaded = st.file_uploader('STRING network TSV', type=['tsv', 'txt'], key='string_network_upload')
        mapping_upload = st.file_uploader('STRING mapping TSV (optional)', type=['tsv', 'txt'], key='string_mapping_upload')
        scale = st.selectbox('Uploaded combined-score scale', [1, 1000], format_func=lambda x: '0–1 (API and website exports)' if x==1 else '0–1000', key='string_upload_scale')
        declared = st.selectbox('Uploaded network type', ['functional', 'physical'], key='string_upload_type')
        st.caption('The selected species applies to the upload. API and website export schemas are accepted. Duplicate/reversed pairs retain the largest score; self-links are removed.')
        if st.button('Import TSV for topology analysis', disabled=uploaded is None, key='string_upload_import'):
            try:
                raw = uploaded.getvalue().decode('utf-8-sig')
                edges = parse_network(raw, TAXA[code], scale)
                resolved = {}
                import_plan = plan
                if mapping_upload:
                    mapping_text = mapping_upload.getvalue().decode('utf-8-sig')
                    source_rows = tsv_rows(mapping_text, ['queryItem', 'stringId'])
                    queries = [row['queryItem'] for row in source_rows]
                    resolved, unresolved = mapping_ids(mapping_text, queries, TAXA[code])
                    # Join uploaded query IDs exactly to candidate IDs or current query aliases.
                    import_plan = candidate_inventory(candidates, code, mapping_export(code)).copy()
                    query_alias = {query: sid for query, sid in resolved.items()}
                    for record in import_plan.to_dict('records'):
                        seq = record['sequence_id']
                        for alias in [seq, seq.split('__')[-1], record['query_id']]:
                            if alias in query_alias:
                                resolved[record['query_id']] = query_alias[alias]
                st.session_state['atlas_string_network'] = {'code': code, 'source': uploaded.name, 'network_type': declared,
                    'edges': edges, 'raw': raw, 'resolved': resolved, 'plan': import_plan,
                    'provenance': {'source_file': uploaded.name, 'sha256': hashlib.sha256(uploaded.getvalue()).hexdigest(),
                                   'taxon': TAXA[code], 'score_scale': scale, 'mapping_file': mapping_upload.name if mapping_upload else '',
                                   'network_type': declared, 'string_version': 'Not recorded in TSV header'}}
            except Exception as error:
                st.error('Unable to import STRING TSV: ' + str(error))
    st.markdown('[STRING API documentation](https://string-db.org/help/api/) · [STRING 12.5](https://version-12-5.string-db.org/)')
    state = st.session_state.get('atlas_string_network')
    if state:
        analysis_panel(state, candidates)
