"""Streamlit interface to the curator's architecture-first prioritization model."""
import hashlib
import json
from pathlib import Path
import zipfile
import io

import pandas as pd
import plotly.express as px
import streamlit as st

from figure_exports import plotly_chart
from prioritize_candidates import rank_catalogue, workbook_bytes, VERSION, SOURCE_SCRIPT_SHA256, ADH_COMPONENTS, FN_COMPONENTS

TIER_COLORS = {'Priority 1': '#08743f', 'Priority 2': '#e2be19', 'Priority 3': '#3376b5',
               'Validation first': '#d34236', 'Evidence needed': '#855a9d', 'Hold': '#6a7470'}
FIRST = ['rank', 'sequence_id', 'protein_annotation_id', 'species_name', 'candidate_annotation', 'family',
         'audit_classification', 'assignment_interpretation', 'priority_group', 'family_orthogroup',
         'orthogroup', 'grade', 'priority_tier', 'priority_score', 'priority_score_upper', 'score_complete',
         'domain_score', 'orthology_score', 'motif_score', 'localization_score', 'evidence_score',
         'conservation_score', 'interface_score', 'network_score', 'fn_architecture_score', 'fn_motif_context_score',
         'host_divergence_score', 'tractability_score', 'conflict_penalty', 'missing_components', 'phylogenetic_support']


def ordered(frame):
    return frame[[column for column in FIRST if column in frame] + [column for column in frame if column not in FIRST]]


@st.cache_data(show_spinner=False, max_entries=12)
def cached_rank(candidates, measured_nodes, mode):
    return rank_catalogue(candidates, measured_nodes, mode)


@st.cache_data(show_spinner=False, max_entries=8)
def cached_workbook(tables, sources):
    return workbook_bytes(tables, sources)


def prioritization_panel(candidates, measured_nodes, key, network_title='Displayed reconstruction'):
    st.markdown('### Architecture-first candidate prioritization')
    st.write('Rank the audited adhesome and FN3 candidates, compare orthogroups, and assemble a balanced experimental panel using the curator’s scoring framework.')
    a, b = st.columns(2)
    scope = a.radio('Prioritization scope', ['All catalogue candidates', 'Candidates in displayed network'], key=key + '_scope')
    mode = b.radio('Network scoring', ['Measured topology', 'Family-role proxy'], key=key + '_mode',
                   help='Measured topology uses the current filtered graph. Family-role proxy reproduces the prioritization model’s role weights and is explicitly labeled.')
    st.caption(network_title + ' · Measured scores use its current node/edge filters. FN3 ranking retains the separate architecture and ligand-context model; network centralities are shown as supporting fields.')
    prepared = candidates.reset_index(drop=True).copy()
    from identifier_labels import identifier_annotations
    annotations = identifier_annotations()
    if len(annotations):
        columns = [column for column in ['sequence_id', 'protein_annotation_id', 'identifier_mapping_status', 'alternative_protein_ids'] if column in annotations]
        annotations = annotations.reset_index(drop=True)[columns].drop_duplicates('sequence_id')
        prepared = prepared.drop(columns=[column for column in columns if column != 'sequence_id'], errors='ignore').merge(annotations, on='sequence_id', how='left', validate='many_to_one')
    if scope == 'Candidates in displayed network':
        ids = set()
        for value in measured_nodes.sequence_id.fillna('') if 'sequence_id' in measured_nodes else []:
            ids.update(identifier.strip() for identifier in str(value).replace(';', '|').split('|') if identifier.strip())
        prepared = prepared[prepared.sequence_id.isin(ids)]
    if prepared.empty:
        st.info('No catalogue candidates map to this scope. Choose all candidates or broaden the network filters.')
        return
    try:
        tables = cached_rank(prepared, measured_nodes, mode)
    except ValueError as error:
        st.error('Prioritization input error: ' + str(error))
        return
    all_ranked = pd.concat([tables['Ranked_adhesome'], tables['Ranked_fibronectin']], ignore_index=True)
    signature = hashlib.sha256((prepared[['sequence_id', 'source']].to_csv(index=False) if 'source' in prepared else prepared.sequence_id.to_csv(index=False)).encode()).hexdigest()[:12]
    filter_key = key + '_' + signature
    a, b, c = st.columns(3)
    species = a.multiselect('Prioritization species', sorted(all_ranked.species_name.unique()), key=filter_key + '_species')
    tiers = b.multiselect('Priority tiers', list(TIER_COLORS), key=filter_key + '_tiers')
    classifications = c.multiselect('Prioritization classification', ['Supported', 'Provisional', 'Unassigned'], default=['Supported', 'Provisional'], key=filter_key + '_classification')
    families = st.multiselect('Prioritization families', sorted(all_ranked.family.unique()), key=filter_key + '_families')
    visible = all_ranked[all_ranked.audit_classification.isin(classifications)]
    if species:
        visible = visible[visible.species_name.isin(species)]
    if tiers:
        visible = visible[visible.priority_tier.isin(tiers)]
    if families:
        visible = visible[visible.family.isin(families)]
    for column, label, value in zip(st.columns(4), ['Candidate assignments', 'Priority 1', 'Priority 2', 'Priority 3'], [len(visible), *(visible.priority_tier.eq(tier).sum() for tier in ['Priority 1', 'Priority 2', 'Priority 3'])]):
        column.metric(label, int(value))
    st.caption('Scores sum available points minus conflicts. Missing contributions stay blank; score upper bounds show the remaining possible points. Priority tiers require the available-evidence score to meet the cutoff and grade A/B with retained architecture. Classification and table filters do not alter scoring or panel selection.')
    tabs = st.tabs(['Ranked adhesome', 'Ranked FN3 candidates', 'Orthogroup priorities', 'Balanced experimental panel', 'Scoring & downloads'])
    for tab, kind in zip(tabs[:2], ['adhesome', 'fibronectin-like']):
        with tab:
            ranked = visible[visible.candidate_class.eq(kind)]
            st.dataframe(ordered(ranked), hide_index=True, width='stretch')
            st.download_button('Download ' + kind + ' priorities · CSV', ordered(ranked).to_csv(index=False), kind + '_priorities.csv', key=key + '_' + kind + '_csv')
            if len(ranked):
                top = ranked.sort_values('priority_score', ascending=False).head(25)
                plotly_chart(px.bar(top, x='priority_score', y='sequence_id', color='priority_tier', color_discrete_map=TIER_COLORS,
                                    orientation='h', hover_data=['family', 'grade', 'priority_score_upper', 'missing_components'], title='Top 25 · ' + kind + ' candidate scores').update_layout(yaxis={'autorange': 'reversed'}, height=800), width='stretch', key=key + '_' + kind + '_plot')
                # Supporting phylogeny is retained even when not an additive score.
                with st.expander('Inspect candidate score and biological evidence'):
                    candidate_key = hashlib.sha256(ranked.sequence_id.to_csv(index=False).encode()).hexdigest()[:10]
                    candidate = st.selectbox('Priority candidate · ' + kind, ranked.sequence_id.tolist(), key=filter_key + '_' + kind + '_' + candidate_key + '_candidate')
                    record = ranked[ranked.sequence_id.eq(candidate)].iloc[0]
                    components = ADH_COMPONENTS if kind == 'adhesome' else FN_COMPONENTS
                    fields = [field for field in [*components, 'conflict_penalty'] if field in record and pd.notna(record[field])]
                    contribution = pd.DataFrame({'component': fields, 'points': [(-1 if field == 'conflict_penalty' else 1) * record[field] for field in fields]})
                    # Evidence is a subtotal in adhesome, not another additive component.
                    if kind == 'adhesome':
                        contribution = contribution[contribution.component.ne('evidence_score')]
                    plotly_chart(px.bar(contribution, x='component', y='points', title='Candidate score contributions'), width='stretch', key=key + '_' + kind + '_contributions')
                    details = [field for field in record.index if field.endswith('_basis') or field in ['architecture', 'architecture_evidence', 'motif_hit_details', 'motif_assignment_tiers', 'topology_compatibility', 'phylogenetic_support', 'motif_conservation', 'host_divergence', 'host_orthology_flag', 'host_similarity_flag', 'interface_connections', 'family_decision', 'assignment_interpretation', 'rationale', 'missing_components', 'eligibility_reason']]
                    st.dataframe(pd.DataFrame({'evidence': details, 'value': [str(record[field]) if pd.notna(record[field]) else 'Not available' for field in details]}), hide_index=True, width='stretch')
            else:
                st.info('No candidates match these display filters.')
    with tabs[2]:
        st.caption('Summaries use the entire selected scope. Alpha-integrin OG0000401 and OG0001220 share a family group; their source orthogroups and all members remain listed.')
        st.dataframe(tables['Orthogroup_summary'], hide_index=True, width='stretch')
        st.download_button('Download orthogroup priorities · CSV', tables['Orthogroup_summary'].to_csv(index=False), 'orthogroup_priorities.csv', key=key + '_groups')
    with tabs[3]:
        st.caption('One eligible group per adhesome role, chosen by species coverage then candidate score. Src, FAK and ILK remain separate. The three FN3 priority groups are selected independently; roles lacking grade A/B candidates are shown explicitly.')
        st.dataframe(tables['Experimental_panel'], hide_index=True, width='stretch')
        st.download_button('Download balanced experimental panel · CSV', tables['Experimental_panel'].to_csv(index=False), 'experimental_panel.csv', key=key + '_panel')
    with tabs[4]:
        st.dataframe(tables['Prioritization_parameters'], hide_index=True, width='stretch')
        st.caption('Phylogenetic branch support and aligned motif conservation accompany every ranked candidate where available. Phylogenetic support breaks score ties; these values are not added again to the workbook’s orthology/motif evidence points. Human orthology affects the explicitly labeled selectivity proxy, not adhesome membership.')
        provenance = {'implementation_version': VERSION, 'adapted_source_script_sha256': SOURCE_SCRIPT_SHA256,
                      'network_mode': mode, 'scope': scope, 'network_context': network_title,
                      'displayed_graph_nodes': len(measured_nodes),
                      'scoring_script_sha256': hashlib.sha256(Path(__file__).with_name('prioritize_candidates.py').read_bytes()).hexdigest(),
                      'candidate_inputs_sha256': hashlib.sha256(prepared.to_csv(index=False).encode()).hexdigest(),
                      'network_metrics_sha256': hashlib.sha256(measured_nodes.to_csv(index=False).encode()).hexdigest(),
                      'source_records': sorted(prepared.source.dropna().unique().tolist()) if 'source' in prepared else []}
        st.download_button('Download prioritization run · JSON', json.dumps(provenance, indent=2), 'prioritization_run.json', 'application/json', key=key + '_run')
        run_table = pd.DataFrame({'parameter': list(provenance), 'value': [json.dumps(value) if isinstance(value, list) else str(value) for value in provenance.values()]})
        export_tables = dict(tables, Prioritization_run=run_table, Network_metrics=measured_nodes)
        sources = {'Source_candidates': prepared}
        if st.button('Prepare complete prioritization workbook', key=key + '_prepare_xlsx'):
            data = cached_workbook(export_tables, sources)
            st.session_state[key + '_xlsx'] = (provenance['candidate_inputs_sha256'], provenance['network_metrics_sha256'], mode, data)
        stored = st.session_state.get(key + '_xlsx')
        if stored and stored[:3] == (provenance['candidate_inputs_sha256'], provenance['network_metrics_sha256'], mode):
            st.download_button('Download complete priorities · XLSX', stored[3], 'candidate_priorities.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key=key + '_xlsx_download')
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, frame in export_tables.items():
                archive.writestr(name + '.csv', frame.to_csv(index=False))
            archive.writestr('Source_candidates.csv', prepared.to_csv(index=False))
            archive.writestr('prioritization_run.json', json.dumps(provenance, indent=2))
        st.download_button('Download complete priorities · CSV ZIP', buffer.getvalue(), 'candidate_priorities.zip', 'application/zip', key=key + '_zip')
        script = Path(__file__).with_name('prioritize_candidates.py')
        st.download_button('Download adapted prioritization script', script.read_bytes(), script.name, 'text/x-python', key=key + '_script')
        st.code('python3 prioritize_candidates.py --network-nodes network_metrics.csv -o candidate_priorities.xlsx\n'
                'python3 prioritize_candidates.py files/adhesome_candidates_list.xlsx --fibronectin files/fibronectin_like_candidate.xlsx --network-mode "Family-role proxy" -o candidate_priorities.xlsx', language='bash')
        st.download_button('Download displayed network metrics · CSV', measured_nodes.to_csv(index=False), 'network_metrics.csv', key=key + '_network_csv')
