"""Motif evidence views backed by the two current candidate workbooks."""

import re

import pandas as pd
import plotly.express as px
import streamlit as st


ADHESOME_SOURCE = 'files/adhesome_candidates_list.xlsx / Motif_annotations'
FN3_SITES_SOURCE = 'files/fibronectin_like_candidate.xlsx / motif_scan_hits'
ELM_SOURCE = 'files/fibronectin_like_candidate.xlsx / ELM_raw_summary'
SITE_PATTERN = re.compile(r'^\s*([^:|]+):(\d+)-(\d+):(.+?)\s+\[([^\]]+)\]\s*$')


def _species(frame):
    frame['species'] = frame.sequence_id.astype(str).str.split('__').str[0].map({
        'Shae': 'S. haematobium', 'Sjap': 'S. japonicum', 'Sman': 'S. mansoni'
    }).fillna('Unknown')
    return frame


def build_motif_tables(books, cohorts):
    """Return screening summaries, positional candidates, and ELM background separately."""
    summary = books['files/adhesome_candidates_list.xlsx']['Motif_annotations'].copy()
    summary['source'] = ADHESOME_SOURCE
    summary = _species(summary)
    summary['collection'] = 'Adhesome priority sites'
    for col in ['raw_match_count', 'distinct_site_count', 'priority_site_count']:
        summary[col] = pd.to_numeric(summary[col], errors='coerce').fillna(0).astype(int)

    adh = cohorts['Adhesome candidates']
    audited = adh[['sequence_id', 'reviewed_family', 'audit_classification']].drop_duplicates('sequence_id')
    summary = summary.merge(audited, on='sequence_id', how='left', validate='many_to_one')
    summary['display_family'] = summary.reviewed_family.combine_first(summary.family)

    parsed = []
    for row in summary.itertuples():
        if pd.isna(row.priority_sites) or not str(row.priority_sites).strip():
            continue
        for token in str(row.priority_sites).split('|'):
            match = SITE_PATTERN.match(token)
            if not match:
                raise ValueError(f'Unrecognized priority motif site for {row.sequence_id}: {token}')
            motif_id, start, end, peptide, tier = match.groups()
            parsed.append({
                'collection': 'Adhesome priority sites', 'source': ADHESOME_SOURCE,
                'sequence_id': row.sequence_id, 'species': row.species,
                'family': row.family, 'display_family': row.display_family,
                'audit_classification': row.audit_classification,
                'motif_id': motif_id, 'motif_name': motif_id, 'start': int(start),
                'end': int(end), 'peptide': peptide, 'candidate_tier': tier,
                'role': 'priority_site', 'functional_hypothesis': row.functional_hypotheses,
                'context_requirements': row.context_requirements,
                'overlapping_domains': row.overlapping_domains,
                'localization': row.deeploc_localizations,
                'topology': row.predicted_topology_segments,
                'partner': '', 'source_url': '', 'primary_reference': ''
            })
    priority = pd.DataFrame(parsed)
    if len(priority) != summary.priority_site_count.sum():
        raise ValueError('Parsed adhesome priority sites disagree with workbook priority_site_count')

    fn3 = books['files/fibronectin_like_candidate.xlsx']['motif_scan_hits'].copy()
    fn3['source'] = FN3_SITES_SOURCE
    fn3['collection'] = 'FN3 curated sites'
    fn3 = _species(fn3)
    fn3_audit = cohorts['FN3 / fibronectin-like review'][
        ['sequence_id', 'reviewed_family', 'audit_classification']
    ].drop_duplicates('sequence_id')
    fn3 = fn3.merge(fn3_audit, on='sequence_id', how='left', validate='many_to_one')
    fn3['display_family'] = fn3.reviewed_family.combine_first(fn3.family)
    fn3['topology'] = ''
    fn3['start'] = pd.to_numeric(fn3.start, errors='coerce').astype('Int64')
    fn3['end'] = pd.to_numeric(fn3.end, errors='coerce').astype('Int64')
    sites = pd.concat([priority, fn3], ignore_index=True, sort=False)
    sites['motif_label'] = sites.motif_id.fillna('').astype(str) + ' · ' + sites.motif_name.fillna('').astype(str)

    elm = books['files/fibronectin_like_candidate.xlsx']['ELM_raw_summary'].copy()
    elm = elm.rename(columns={'protein_id': 'sequence_id'})
    elm['source'] = ELM_SOURCE
    elm = _species(elm)
    elm = elm.merge(fn3_audit, on='sequence_id', how='left', validate='many_to_one')
    elm['display_family'] = elm.reviewed_family.fillna('FN3 review / other')
    return summary, sites, elm


def _filtered(frame, species, families, query):
    selected = frame[frame.species.isin(species)].copy()
    if families:
        selected = selected[selected.display_family.isin(families)]
    if query:
        q = query.casefold()
        selected = selected[selected.sequence_id.astype(str).str.casefold().str.contains(q, regex=False)
                            | selected.display_family.fillna('').astype(str).str.casefold().str.contains(q, regex=False)]
    return selected


def motif_panel(summary, sites, elm, chart, table, download):
    st.subheader('Motif evidence explorer')
    st.write('Explore **positional motif candidates**, protein-level **screening summaries**, and the broader **ELM regex background** from the current candidate workbooks. These are different evidence units and are shown separately.')
    st.caption('This explorer uses both workbooks independently of the catalogue sidebar collection and protein filters.')

    species_options = sorted(set(summary.species) | set(sites.species) | set(elm.species))
    family_options = sorted(set(summary.display_family.dropna()) | set(sites.display_family.dropna()) | set(elm.display_family.dropna()))
    c1, c2 = st.columns(2)
    with c1:
        species = st.multiselect('Species in motif explorer', species_options, default=species_options, key='motif_species')
    with c2:
        families = st.multiselect('Reviewed families / screening classes', family_options, key='motif_families')
    query = st.text_input('Find a protein or family', placeholder='Smp_126140, PINCH, collagen…', key='motif_query')
    sm = _filtered(summary, species, families, query)
    si = _filtered(sites, species, families, query)
    em = _filtered(elm, species, families, query)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Proteins in adhesome motif screen', f'{sm.sequence_id.nunique():,}')
    m2.metric('Adhesome priority sites', f'{(si.collection == "Adhesome priority sites").sum():,}')
    m3.metric('FN3 annotated sites', f'{(si.collection == "FN3 curated sites").sum():,}')
    m4.metric('FN3 proteins in ELM screen', f'{em.sequence_id.nunique():,}')

    overview, position_tab, summary_tab, elm_tab = st.tabs([
        'Overview', 'Positional motif sites', 'Adhesome screening summaries', 'FN3 ELM background'
    ])
    with overview:
        if si.empty:
            st.info('No positional sites match these filters. The screening summary and ELM tabs may still contain records.')
        else:
            left, right = st.columns(2)
            with left:
                family_counts = (si.groupby(['display_family', 'collection'], dropna=False).size()
                                 .reset_index(name='sites').sort_values('sites', ascending=False).head(25))
                chart(px.bar(family_counts, x='sites', y='display_family', color='collection',
                             orientation='h', title='Positional sites by family and source',
                             labels={'display_family': 'Reviewed family / screening class'},
                             height=max(420, 24 * family_counts.display_family.nunique())))
            with right:
                tiers = si.groupby(['candidate_tier', 'collection'], dropna=False).size().reset_index(name='sites')
                chart(px.bar(tiers, x='candidate_tier', y='sites', color='collection',
                             barmode='group', title='Site context tiers',
                             labels={'candidate_tier': 'Candidate tier'}))
        st.caption('The site charts count individual coordinates. The workbook screening counts represent raw sequence-pattern matches and are not added to site counts.')

    with position_tab:
        collection = st.multiselect('Site source', sorted(sites.collection.dropna().unique()),
                                    default=sorted(sites.collection.dropna().unique()), key='motif_site_sources')
        subset = si[si.collection.isin(collection)].copy()
        motif_ids = sorted(subset.motif_id.dropna().astype(str).unique())
        c1, c2 = st.columns(2)
        with c1:
            chosen_ids = st.multiselect('Motif IDs', motif_ids, key='motif_site_ids')
        with c2:
            tiers = st.multiselect('Site context tiers', sorted(subset.candidate_tier.dropna().astype(str).unique()), key='motif_site_tiers')
        if chosen_ids:
            subset = subset[subset.motif_id.isin(chosen_ids)]
        if tiers:
            subset = subset[subset.candidate_tier.isin(tiers)]
        st.caption(f'{len(subset):,} positional sites in {subset.sequence_id.nunique():,} proteins. Coordinates are 1-based and inclusive.')
        if subset.empty:
            st.info('No positional sites match the selected filters.')
        else:
            protein_counts = subset.groupby(['sequence_id', 'collection']).size().reset_index(name='sites')
            top_ids = protein_counts.groupby('sequence_id').sites.sum().nlargest(20).index
            chart(px.bar(protein_counts[protein_counts.sequence_id.isin(top_ids)], x='sites', y='sequence_id',
                         color='collection', orientation='h', title='Proteins with the most displayed sites',
                         height=max(420, 23 * len(top_ids))))
            selected_protein = st.selectbox('Inspect motif positions for a protein',
                                            ['— Select protein —'] + sorted(subset.sequence_id.unique()), key='motif_position_protein')
            if selected_protein != '— Select protein —':
                one = subset[subset.sequence_id.eq(selected_protein)]
                fig = px.scatter(one, x='start', y='motif_id', color='candidate_tier', symbol='collection',
                                 hover_data=['end', 'peptide', 'display_family', 'functional_hypothesis'],
                                 title=f'Motif positions · {selected_protein}', labels={'start': 'Residue position'})
                fig.update_traces(marker={'size': 13})
                chart(fig)
            visible = [c for c in ['collection', 'species', 'sequence_id', 'display_family', 'family',
                                   'audit_classification', 'motif_id', 'motif_name', 'start', 'end',
                                   'peptide', 'candidate_tier', 'role', 'functional_hypothesis',
                                   'partner', 'overlapping_domains', 'localization', 'context_requirements',
                                   'supported_criteria', 'missing_or_conflicting_criteria', 'source_url',
                                   'primary_reference', 'source'] if c in subset]
            table(subset[visible].sort_values(['sequence_id', 'start']))
            download(subset, 'motif_positional_sites.csv')

    with summary_tab:
        st.write('One record per **protein–family screening hypothesis** from `Motif_annotations`. Priority sites are parsed into the positional tab; raw match and distinct site counts summarize the broader screen.')
        if sm.empty:
            st.info('No adhesome screening summaries match these filters.')
        else:
            a, b, c = st.columns(3)
            a.metric('Protein–family records', f'{len(sm):,}')
            b.metric('Raw pattern matches', f'{sm.raw_match_count.sum():,}')
            c.metric('Distinct matched positions', f'{sm.distinct_site_count.sum():,}')
            cols = [x for x in ['species', 'sequence_id', 'display_family', 'family', 'audit_classification',
                                'in_catalogue', 'raw_match_count', 'distinct_site_count', 'priority_site_count',
                                'library_ids', 'candidate_tiers', 'priority_sites', 'overlapping_domains',
                                'predicted_topology_segments', 'deeploc_localizations', 'signalp_predictions',
                                'context_requirements', 'functional_hypotheses', 'source'] if x in sm]
            table(sm[cols].sort_values(['priority_site_count', 'raw_match_count'], ascending=False))
            download(sm, 'adhesome_motif_screening_summaries.csv')

    with elm_tab:
        st.write('The `ELM_raw_summary` sheet records broad ELM sequence-pattern matches for FN3 candidates. These matches have not been elevated to context-supported positional candidates; the curated FN3 annotations are in the positional tab.')
        if em.empty:
            st.info('No FN3 ELM summaries match these filters.')
        else:
            a, b, c = st.columns(3)
            a.metric('ELM-screened proteins', f'{em.sequence_id.nunique():,}')
            b.metric('Raw ELM matches', f'{pd.to_numeric(em.ELM_unverified_match_count, errors="coerce").sum():,.0f}')
            c.metric('Distinct ELM positions', f'{pd.to_numeric(em.ELM_unique_site_count, errors="coerce").sum():,.0f}')
            cols = [x for x in ['species', 'sequence_id', 'display_family', 'audit_classification',
                                'ELM_unverified_match_count', 'ELM_unique_site_count',
                                'ELM_distinct_class_count', 'ELM_top5_class_hits',
                                'curated_annotation_records', 'curated_unique_sites',
                                'ELM_evidence_status', 'source'] if x in em]
            table(em[cols].sort_values('ELM_unverified_match_count', ascending=False))
            download(em, 'fn3_elm_raw_summary.csv')
