"""Literature evidence panels shared by the Atlas views."""

import pandas as pd
import streamlit as st

from literature import evidence_for, registry_exports

SCOPES = {
    'exact_protein_id':'Published accession correspondence',
    'published_named_protein':'Published named-protein correspondence',
    'genomic_candidate_mentioned':'Genomic candidate discussed in the study',
    'named_locus_context':'Named locus context',
    'published_correspondence_pending':'Published correspondence pending',
    'family_level':'Family evidence',
    'pathway_level':'Pathway context',
    'cross_species_family_context':'Comparative family context',
    'source_family_changed':'Previous family context',
    'general_metazoan_mechanism':'Metazoan mechanism',
}


def reference_card(ref, label='', note=''):
    st.markdown(f"**{ref['reference_id']} · {ref['authors']} ({ref['year']})** — {ref['title']}")
    st.caption(' · '.join(filter(None, [label, ref['evidence_origin'].replace('_', ' '),
                 ', '.join(ref['study_species']), ref['experimental_methods']])))
    st.write(ref['experimental_finding'])
    if note:
        st.caption(note)
    if ref['reference_verification_status']=='unverified':
        st.caption('Bibliographic identifiers awaiting verification.')
    st.markdown(f"[DOI]({ref['doi_url']}) · [PubMed]({ref['pubmed_url']})")


def evidence_panel(registry, family, protein_id=''):
    links = evidence_for(registry, family, protein_id)
    if not links:
        st.caption('Molecular evidence for this selection is available in the annotation and domain views.')
        return
    for link in links:
        reference_card(registry['references'][link['reference_id']],
                       SCOPES[link['match_level']], link.get('note', ''))


def registry_panel(registry):
    st.header('Literature and biological evidence')
    mode = st.selectbox('Evidence section', ['Publications', 'Protein correspondence', 'Family and pathway context'])
    refs = registry['references']
    if mode == 'Publications':
        origin = st.selectbox('Evidence origin', ['All'] + sorted({ref['evidence_origin'] for ref in refs.values()}))
        query = st.text_input('Search studies', placeholder='Reference ID, publication, protein or pathway').casefold()
        for ref in refs.values():
            if (origin == 'All' or origin == ref['evidence_origin']) and query in str(ref).casefold():
                reference_card(ref)
    elif mode == 'Protein correspondence':
        st.dataframe(pd.DataFrame(registry['mapping_audit']), hide_index=True, width='stretch')
    else:
        st.dataframe(pd.DataFrame(registry['family_index']), hide_index=True, width='stretch')
        pathways = sorted({path for ref in refs.values() for path in ref['linked_pathways']})
        pathway = st.selectbox('Pathway', pathways, format_func=lambda value: value.replace('_', ' '))
        for ref in refs.values():
            if pathway in ref['linked_pathways']:
                reference_card(ref)
    with st.expander('Download evidence and provenance'):
        for name, data in registry_exports(registry).items():
            mime = 'application/json' if name.endswith('.json') else 'text/tab-separated-values'
            st.download_button('Download '+name, data, name, mime, key='literature_download_'+name)


def interaction_panel(registry):
    st.subheader('Published interactions and simulator mechanisms')
    origins = sorted({row['evidence_origin'] for row in registry['interactions']})
    origin = st.selectbox('Interaction evidence origin', ['All'] + origins)
    kinds = ['All', 'Published relationships', 'Reference-family projections', 'Simulated state transitions']
    kind = st.selectbox('Relationship class', kinds)
    rows = []
    for row in registry['interactions']:
        row_class = ('Reference-family projections' if row['is_reference_projected'] else
                     'Simulated state transitions' if row['interaction_type'] == 'Simulated state transition'
                     else 'Published relationships')
        if (origin == 'All' or row['evidence_origin'] == origin) and (kind == 'All' or row_class == kind):
            rows.append(row)
    if rows:
        by_id = {row['interaction_id']:row for row in rows}
        choice = st.selectbox('Inspect an evidence record', list(by_id),
                              format_func=lambda key: ' · '.join([key, by_id[key]['source_component'],
                              by_id[key]['target_component'], by_id[key]['interaction_type']]))
        row = by_id[choice]
        st.write(row['evidence_description'])
        st.caption(row['evidence_origin'].replace('_', ' ') + ' · ' + row['molecular_role'])
        if row['simulator_rule_id']:
            st.caption('Simulator rule ' + row['simulator_rule_id'])
        for rid in row['literature_reference_ids']:
            reference_card(registry['references'][rid])
        if row.get('source_pmids'):
            st.markdown(' · '.join(f'[PMID {pid}](https://pubmed.ncbi.nlm.nih.gov/{pid}/)'
                                   for pid in row['source_pmids']))
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
    st.download_button('Download interaction evidence TSV', registry_exports(registry)['interaction_evidence.tsv'],
                       'interaction_evidence.tsv', 'text/tab-separated-values')
