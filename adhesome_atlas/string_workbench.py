"""Candidate selection, STRING API queries and session-scoped TSV topology."""
import hashlib
from decimal import Decimal
import io
import json
from pathlib import Path
import re
import time
import pandas as pd
import streamlit as st
from data import SPECIES
from family_merges import atlas_group
from figure_exports import plotly_chart
from networks import mapping_export
from string_fetch import BASE, api_url, api_request, parameters, network_parameters, mapping_ids, tsv_rows, resolve_proteins
from string_analysis import register_network

TAXA = {'Shae': 6185, 'Sjap': 6182, 'Sman': 6183}


def mapping_table(frame):
    shown=frame.copy()
    if 'E-value' in shown:shown['E-value']=pd.to_numeric(shown['E-value'],errors='coerce')
    st.dataframe(shown,hide_index=True,width='stretch',column_config={
        'E-value':st.column_config.NumberColumn('E-value',format='scientific')})


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


def annotations_for_nodes(identifiers, candidates, local_mapping, plan, api_mapping, code, taxon=None):
    taxon=TAXA.get(code) if taxon is None else taxon
    links = {}
    for record in local_mapping.to_dict('records'):
        seq = record['queryItem']
        if not seq.startswith(code + '__'):
            seq = code + '__' + seq
        links.setdefault(record['stringId'], set()).add(seq)
    for record in plan.to_dict('records'):
        query = record['query_id']
        sid = api_mapping.get(record['sequence_id'],api_mapping.get(query, query if query.startswith(str(taxon) + '.') else ''))
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
                     'Family': join('reviewed_family') or join('family') or 'Unmapped', 'orthogroup': join('orthogroup'),
                     'candidate_annotation': join('candidate_annotation'), 'species': SPECIES[code],
                     'mapping_status': 'Many candidates share STRING representative' if len(seqs) > 1 else 'Mapped candidate' if seqs else 'Additional / unmapped STRING protein',
                     'layer': 'Unresolved'})
    return pd.DataFrame(rows, columns=['identifier', 'sequence_id', 'Family', 'orthogroup', 'candidate_annotation', 'species', 'mapping_status', 'layer'])


def analysis_panel(state,candidates,key='string_import_'):
    from string_analysis_view import analysis_panel as render
    render(state,candidates,key)


def string_panel(candidates,sequences=None):
    sequences=sequences or {}
    st.markdown('### STRING query & TSV import')
    st.write('Choose catalogue families or orthogroups, resolve their proteins in STRING 12.5, and import the returned associations for interactive topology analysis.')
    code = st.selectbox('STRING query species', list(SPECIES), format_func=SPECIES.get, key='string_query_species')
    TAXA[code]=int(st.number_input('STRING species taxon ID',min_value=0,value=TAXA.get(code,0),step=1,help='Enter the NCBI taxon ID recognized by STRING for this species. Coverage depends on the STRING release. No cross-species substitution is made.'))
    if not TAXA[code]:
        st.info('Enter a STRING taxon ID to prepare queries or import a species network.')
        from string_analysis_view import saved_networks_panel
        saved_networks_panel(candidates)
        return
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
    mode_label=st.selectbox('STRING protein mapping',[
        'Protein sequences (recommended)','Identifiers + sequence fallback','Identifiers only'],
        help='Sequence mode submits the original amino-acid FASTA to STRING similarity search, avoiding unrecognized Atlas gene IDs.')
    mode={'Protein sequences (recommended)':'sequences','Identifiers + sequence fallback':'auto','Identifiers only':'identifiers'}[mode_label]
    if mode=='sequences':
        plan['query_id']=plan.sequence_id
        plan['query_basis']='Original protein sequence · STRING similarity search'
    plan['sequence_length']=plan.sequence_id.map(lambda identifier:len(sequences.get(identifier,'')))
    query_sequences={row.query_id:sequences[row.sequence_id] for row in plan.itertuples() if sequences.get(row.sequence_id)}
    min_identity,max_evalue,min_score_gap=80,1e-5,.05
    if mode!='identifiers':
        with st.expander('Sequence mapping criteria'):
            st.caption('A unique highest-bitscore representative is mapped after these filters. Every alignment hit is retained. Identity describes the returned alignment; full-length coverage is not reported by this STRING endpoint.')
            aa,bb,cc=st.columns(3)
            min_identity=aa.number_input('Minimum alignment identity (%)',0.0,100.0,80.0,1.0)
            max_evalue=bb.number_input('Maximum alignment E-value',min_value=1e-300,max_value=1.0,value=1e-5,format='%.1e')
            min_score_gap=cc.number_input('Minimum bitscore gap (%)',0.0,100.0,5.0,1.0)/100
    identifiers = sorted(set(plan.query_id))
    st.caption(f'{plan.sequence_id.nunique()} candidate proteins → {len(identifiers)} unique queries · taxon {TAXA[code]} · {len(query_sequences)} original sequences available. Families and orthogroups select their protein members.')
    cols = [name for name in ['sequence_id', 'candidate_annotation', 'query_family', 'audit_classification', 'query_orthogroup', 'query_id', 'query_basis','sequence_length'] if name in plan]
    with st.expander('Selected candidates and STRING query mapping', expanded=bool(identifiers)):
        st.dataframe(plan[cols], width='stretch', hide_index=True)
    a, b, c = st.columns(3)
    score = a.slider('STRING required score (0–1000)', 0, 1000, 400, 10, key='string_query_score')
    extra = b.number_input('Additional STRING neighbors', min_value=0, max_value=100, value=0, key='string_query_extra')
    network_type = c.selectbox('STRING network type', ['functional', 'physical'], key='string_query_type')
    if identifiers:
        config = {'species': TAXA[code], 'identifiers': identifiers, 'score': score, 'add_nodes': int(extra), 'network_type': network_type,
                  'candidate_selection': plan[cols].to_dict('records'), 'string_version': '12.5','mapping_mode':mode,
                  'sequences':query_sequences if mode!='identifiers' else {},
                  'sequence_thresholds':{'min_identity':min_identity,'max_evalue':max_evalue,'min_score_gap':min_score_gap}}
        mapping_signature={key:config[key] for key in ['species','identifiers','mapping_mode','sequence_thresholds']}
        mapping_signature['sequence_hashes']={query:hashlib.sha256(sequence.encode()).hexdigest() for query,sequence in config['sequences'].items()}
        signature = hashlib.sha256(json.dumps(mapping_signature,sort_keys=True).encode()).hexdigest()
        map_params = parameters(identifiers, TAXA[code], echo_query=1)
        with st.expander('STRING requests, original FASTA and WSL script'):
            if mode!='identifiers':
                st.code('POST '+BASE+'/api/json/similarity_search\nspecies='+str(TAXA[code])+'\nsequences=<original protein FASTA>',language='text')
                fasta=''.join('>'+identifier+'\n'+sequence+'\n' for identifier,sequence in query_sequences.items())
                st.download_button('Download selected original protein sequences · FASTA',fasta,'string_selected_candidates.faa','text/plain',key='string_sequence_fasta')
            if mode!='sequences':
                st.code(api_url('get_string_ids', map_params), language='text')
                if len(api_url('get_string_ids', map_params)) <= 1800:
                    st.link_button('Open STRING identifier mapping TSV', api_url('get_string_ids', map_params))
            st.download_button('Download STRING query configuration', json.dumps(config, indent=2), 'string_query.json', 'application/json', key='string_query_config')
            script = Path(__file__).with_name('string_fetch.py')
            st.download_button('Download STRING query script', script.read_bytes(), script.name, 'text/x-python', key='string_query_script')
            st.code('python3 string_fetch.py string_query.json --output STRING_results --fetch', language='bash')
            st.caption('Sequences use POST to the STRING similarity-search endpoint. Identifier queries use GET for short lists and POST for long lists. The configuration includes the original sequences and selected mapping criteria. Requests are sequential, one second apart; mapping, all alignment hits, network TSV and provenance are saved.')
        if st.button('1 · Resolve selected proteins in STRING', key='string_query_resolve'):
            try:
                with st.spinner('Mapping selected proteins in STRING 12.5…'):
                    progress=st.empty()
                    result=resolve_proteins(identifiers,TAXA[code],query_sequences,mode,min_identity,max_evalue,min_score_gap,progress=progress.caption)
                    progress.empty()
                st.session_state['atlas_string_mapping'] = {'signature': signature,**result}
            except Exception as error:
                st.error('STRING mapping failed: ' + str(error))
        mapping = st.session_state.get('atlas_string_mapping')
        if mapping and mapping['signature'] == signature:
            st.success(f'{len(mapping["resolved"])} proteins mapped; {len(mapping["unresolved"])} unresolved.')
            with st.expander('Resolved STRING protein mapping', expanded=True):
                mapping_table(pd.DataFrame(tsv_rows(mapping['raw'], ['queryItem', 'stringId'])))
            if mapping['unresolved']:
                st.dataframe(pd.DataFrame([{'query':query,'status':mapping['status_by_query'].get(query,'Unresolved')} for query in mapping['unresolved']]),hide_index=True,width='stretch')
            if mapping.get('sequence_hits'):
                with st.expander('Sequence alignments · selected and alternative STRING representatives'):
                    hits=pd.DataFrame(mapping['sequence_hits'])
                    mapping_table(hits)
                    export_hits=hits.copy();export_hits['E-value']=export_hits['E-value'].map(lambda value:'' if pd.isna(value) or value=='' else format(Decimal(str(value)),'e'))
                    st.download_button('Download all sequence alignment hits · TSV',export_hits.to_csv(sep='\t',index=False),'string_sequence_hits.tsv','text/tab-separated-values')
            st.download_button('Download STRING mapping provenance',json.dumps(mapping['log'],indent=2),'string_mapping_run.json','application/json')
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
                        network_state = {'code': code,'taxon':TAXA[code], 'source': 'STRING 12.5 API', 'network_type': network_type,
                            'edges': edges, 'raw': raw, 'resolved': mapping['resolved'], 'plan': plan,
                            'provenance': {'config': config, 'mapping_request': mapping['log'], 'network_request': log, 'unresolved': mapping['unresolved'],
                                'resolved_mapping':mapping['resolved'],'mapping_status':mapping['status_by_query'],'sequence_hits':mapping.get('sequence_hits',[])}}
                        register_network(st.session_state,network_state)
                    except Exception as error:
                        st.error('STRING network fetch failed: ' + str(error))
    else:
        st.info('Select one or more families or orthogroups to create a STRING query. Existing TSVs can also be imported below.')
    with st.expander('Import a STRING TSV from your computer', expanded=not identifiers):
        uploads = st.file_uploader('STRING network TSV', type=['tsv', 'txt'], accept_multiple_files=True, key='string_network_upload')
        mapping_upload = st.file_uploader('STRING mapping TSV (optional)', type=['tsv', 'txt'], key='string_mapping_upload')
        scale = st.selectbox('Uploaded combined-score scale', [1, 1000], format_func=lambda x: '0–1 (API and website exports)' if x==1 else '0–1000', key='string_upload_scale')
        declared = st.selectbox('Uploaded network type', ['functional', 'physical'], key='string_upload_type')
        st.caption('Select one or more network files. All files in this batch use the selected species and score scale; import other species as a separate batch. Every valid network is saved independently. API and website export schemas are accepted. Duplicate/reversed pairs retain the largest score; self-links are removed.')
        if st.button('Import TSV for topology analysis', disabled=not uploads, key='string_upload_import'):
            for uploaded in uploads:
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
                    network_state = {'code': code,'taxon':TAXA[code], 'source': uploaded.name, 'network_type': declared,
                        'edges': edges, 'raw': raw, 'resolved': resolved, 'plan': import_plan,
                        'provenance': {'source_file': uploaded.name, 'sha256': hashlib.sha256(uploaded.getvalue()).hexdigest(),
                                       'taxon': TAXA[code], 'score_scale': scale, 'mapping_file': mapping_upload.name if mapping_upload else '',
                                       'network_type': declared, 'string_version': 'Not recorded in TSV header'}}
                    register_network(st.session_state,network_state)
                    st.success('Imported '+uploaded.name+' · '+str(len(edges))+' unique associations')
                except Exception as error:
                    st.error('Unable to import '+uploaded.name+': ' + str(error))
    st.markdown('[STRING API documentation](https://string-db.org/help/api/) · [STRING 12.5](https://version-12-5.string-db.org/)')
    from string_analysis_view import saved_networks_panel
    saved_networks_panel(candidates)
