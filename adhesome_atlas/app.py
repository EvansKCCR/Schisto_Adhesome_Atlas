from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data import ROOT, load, fingerprint, intervals, state_intervals, fasta_export, source_files
from networks import network_panel
from networks import load_network
from reconstruction import reconstruction_panel
from orthology_views import evidence_view, priority_view
from phylogeny_view import phylogeny_panel
from branding import identity_banner, creator_credit

st.set_page_config(page_title='Schisto-Adhesome Atlas | Integrin–adhesome', page_icon='🧬', layout='wide')
st.markdown('''<style>
.block-container{padding-top:2rem;max-width:1500px}
.hero{background:linear-gradient(115deg,#112d43,#125e70 65%,#148b8b);color:white;padding:32px 38px;border-radius:20px;margin-bottom:24px}
.hero h1{color:white;font-size:2.7rem;margin:4px 0 10px;letter-spacing:-1.5px}
.hero p{color:#d8eeee;max-width:780px;font-size:1.05rem}
.eyebrow{font-size:.72rem;letter-spacing:3px;text-transform:uppercase;color:#a6e3df}
[data-testid="stMetric"]{background:white;border:1px solid #dce6ed;border-radius:14px;padding:16px}
[data-testid="stSidebar"]{border-right:1px solid #dce6ed}
</style>''', unsafe_allow_html=True)

@st.cache_data(show_spinner='Reading annotation and evidence library…')
def cached_data(signature):
    return load()

try:
    cohorts, books, motifs, sequences, memberships, raw, topologies, conflicts = cached_data(fingerprint())
except Exception as exc:
    st.error(f'Unable to read annotation library at {ROOT}: {exc}')
    st.stop()

with st.sidebar:
    st.markdown('## 🧬 Schisto-Adhesome Atlas')
    st.caption('INTEGRIN · ADHESOME · EVIDENCE')
    section = st.radio('Explore', ['Introduction', 'Components', 'Interactions', 'Phylogeny', 'Source Library', 'Protein dossier', 'Motif explorer', 'Citations'])
    page = section
    if section == 'Components':
        page = st.radio('Component view', ['Summary statistics', 'Summary graphs', 'Candidate catalogue', 'Comparative lab', 'Orthology & evidence', 'FN3 / RPTP priorities'])
    st.divider()
    cohort = st.selectbox('Collection', list(cohorts))
    base = cohorts[cohort]
    species = st.multiselect('Species', sorted(base.species.unique()), default=sorted(base.species.unique()))
    families = st.multiselect('Families / screening classes', sorted(base.family.dropna().unique()))
    statuses = st.multiselect('Source status', sorted(base.status.dropna().unique()))
    query = st.text_input('Search annotations', placeholder='Protein ID, PF00373, talin…')
    st.caption('Empty family/status selections include all. Clear species to show no records.')
    if st.button('Reload source files'):
        st.cache_data.clear()
        st.rerun()

df = base[base.species.isin(species)].copy()
if families:
    df = df[df.family.isin(families)]
if statuses:
    df = df[df.status.isin(statuses)]
if query:
    df = df[df.fillna('').astype(str).apply(lambda c: c.str.contains(query, case=False, regex=False)).any(axis=1)]
ids = set(df.sequence_id)
network_candidates = pd.concat([cohorts['Adhesome candidates'],cohorts['FN3 / fibronectin-like review']],ignore_index=True)
hits = motifs[motifs.sequence_id.isin(ids)]
palette = ['#087f8c', '#dd8751', '#6976b8', '#69a893', '#bb6590', '#99a9b7']

def chart(fig):
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#18354a', margin=dict(l=12,r=12,t=45,b=20), colorway=palette)
    st.plotly_chart(fig, width='stretch', config={'displaylogo': False})

def table(frame):
    # Mixed Excel cells remain legible without Arrow mixed-type inference failures.
    out = frame.copy()
    out.columns = out.columns.map(str)
    for c in out:
        if out[c].dtype == object:
            out[c] = out[c].map(lambda v: None if pd.isna(v) else str(v))
    st.dataframe(out, width='stretch', hide_index=True)

def download(frame, name):
    st.download_button('↓ Download table · CSV', frame.to_csv(index=False).encode('utf-8-sig'), name, 'text/csv')

identity_banner()
st.markdown('<div class="hero"><div class="eyebrow">Comparative molecular atlas · Schistosoma</div><h1>Schisto-Adhesome Atlas</h1><p>Explore integrin–adhesome candidates across three schistosome species, from family hypotheses to domains, sequence motifs and localization evidence.</p></div>', unsafe_allow_html=True)
st.caption(f'{cohort}  /  {len(df):,} filtered hypothesis records  /  {df.sequence_id.nunique():,} distinct proteins')

if page not in ['Source Library', 'Interactions', 'Introduction', 'Citations', 'FN3 / RPTP priorities', 'Phylogeny'] and df.empty:
    st.info('No candidates match these filters. Select a species or broaden your search.')
    st.stop()

if page == 'Introduction':
    st.subheader('About the Schisto-Adhesome Atlas')
    st.write('A comparative catalogue of integrin–adhesome candidates in S. haematobium, S. japonicum and S. mansoni. Explore protein families, domain architectures, localization predictions and the supplied STRING association networks.')
    st.caption('Collection totals below describe all records in each source collection. The filtered selection is shown above. Network species and score controls are independent.')
    for col, label, frame in zip(st.columns(3), cohorts.keys(), cohorts.values()):
        col.metric(label, f'{frame.sequence_id.nunique():,} proteins', f'{len(frame):,} hypothesis records', delta_color='off')
    st.markdown('### Network graphs')
    reconstruction_panel(network_candidates, load_network, 'intro_reconstruction_')

elif page == 'Phylogeny':
    phylogeny_panel()

elif page == 'Interactions':
    mode = st.radio('Network workspace', ['Unified reconstruction', 'Species STRING explorer'], horizontal=True)
    if mode == 'Unified reconstruction':
        reconstruction_panel(network_candidates, load_network, 'reconstruction_')
    else:
        network_panel(network_candidates, 'interactions_', detailed=True)

elif page == 'Orthology & evidence':
    evidence_view(df)

elif page == 'FN3 / RPTP priorities':
    priority_view(cohorts['FN3 / fibronectin-like review'])

elif page == 'Summary statistics':
    st.subheader('Components · Summary statistics')
    unique = df.drop_duplicates('sequence_id')
    summary = df.groupby('species').agg(hypothesis_records=('sequence_id','size'), distinct_proteins=('sequence_id','nunique'), family_labels=('family','nunique')).reset_index()
    lengths = unique.groupby('species').length.agg(['median','min','max']).rename(columns={'median':'median_length_aa','min':'minimum_length_aa','max':'maximum_length_aa'})
    summary = summary.join(lengths,on='species')
    summary['proteins_with_sequence'] = summary.species.map(unique.assign(available=unique.sequence_id.isin(sequences)).groupby('species').available.sum())
    table(summary)
    download(summary,'component_summary_statistics.csv')
    st.markdown('### Family and status counts')
    counts = df.groupby(['species','family','status']).sequence_id.nunique().reset_index(name='distinct_proteins')
    table(counts)
    st.caption('Length summaries use one record per protein. Family and status groups may overlap; they are not additive protein totals. Sequence availability reflects only the files currently supplied.')

elif page == 'Summary graphs':
    st.subheader('Components · Summary graphs')
    cols = st.columns(4)
    for col, label, value in zip(cols, ['Distinct proteins', 'Family / class labels', 'Species represented', 'Proteins with motif hits'], [len(ids), df.family.nunique(), df.species.nunique(), hits.sequence_id.nunique()]):
        col.metric(label, f'{value:,}')
    st.markdown('### A landscape of adhesion candidates')
    left, right = st.columns([1.35, 1])
    with left:
        summary = df.groupby(['module','family']).sequence_id.nunique().reset_index(name='proteins')
        chart(px.treemap(summary, path=['module','family'], values='proteins', color='module', color_discrete_sequence=palette, title='Explore modules → families'))
    with right:
        counts = df.groupby(['species','status']).sequence_id.nunique().reset_index(name='proteins')
        chart(px.bar(counts, x='species', y='proteins', color='status', barmode='group', color_discrete_sequence=palette, title='Candidate status across species'))
    st.info('Counts are distinct proteins within each plotted group. A protein may have multiple family hypotheses, so group totals can exceed the collection’s distinct-protein count. Source status is retained; it does not establish experimental function or orthology.')
    st.markdown('### Follow the evidence')
    for col, title, body in zip(st.columns(3), ['01 / Find a candidate', '02 / Inspect its architecture', '03 / Compare the repertoire'], ['Search identifiers, families and Pfam annotations in the catalogue.', 'Open a dossier for positional domains, motifs, topology and raw predictor results.', 'Compare species using absolute counts or within-species family representation.']):
        with col:
            st.markdown(f'**{title}**')
            st.write(body)

elif page == 'Candidate catalogue':
    st.subheader('Candidate catalogue')
    defaults = [c for c in ['sequence_id','species','family','assigned_family','module','status','length','architecture','DeepLoc_2.1','orthogroup','evidence_review_stage','priority_group'] if c in df]
    columns = st.multiselect('Visible annotation fields', list(df.columns), default=defaults)
    table(df[columns])
    a,b = st.columns(2)
    with a:
        download(df, 'filtered_candidates.csv')
    with b:
        st.download_button('↓ Filtered proteins · FASTA', fasta_export(df.sequence_id, sequences), 'filtered_proteins.fasta', 'text/plain')
    st.caption(f'{len(ids.intersection(sequences)):,} of {len(ids):,} filtered proteins have a source sequence. FASTA exports deduplicate protein IDs; CSV retains each hypothesis.')

elif page == 'Protein dossier':
    key = st.selectbox('Protein', sorted(ids))
    records = df[df.sequence_id.eq(key)]
    row = records.iloc[0]
    st.subheader(key)
    st.write(f"{row.species} · {' / '.join(records.family.unique())}")
    seq = sequences.get(key, '')
    a,b,c = st.columns(3)
    a.metric('Sequence length', f'{len(seq):,} aa' if seq else 'Unavailable')
    b.metric('Family hypotheses in selection', len(records))
    local_hits = motifs[motifs.sequence_id.eq(key)]
    c.metric('Reported motif hits', len(local_hits))
    tracks = []
    for architecture in records.architecture.dropna().unique():
        tracks.extend([dict(track='Pfam', label=n, start=s, end=e) for n,s,e in intervals(architecture)])
    for name, evidence in raw.items():
        if 'CDD' in name:
            for _, r in evidence[evidence.sequence_id.eq(key) & evidence['Hit type'].eq('specific')].iterrows():
                tracks.append(dict(track='CDD · specific', label=r['Short name'], start=r['From'], end=r['To']))
    tracks.extend(dict(track='Motif · predicted',label=r.elm_class,start=r.start,end=r.end) for r in local_hits.itertuples())
    tracks.extend(dict(track='Topology',label=n,start=s,end=e) for n,s,e in state_intervals(topologies.get(key,'')))
    st.markdown('### Sequence architecture')
    if tracks:
        fig = go.Figure()
        for i, track in enumerate(dict.fromkeys(t['track'] for t in tracks)):
            subset = [t for t in tracks if t['track']==track]
            fig.add_trace(go.Bar(y=[track]*len(subset), x=[t['end']-t['start']+1 for t in subset], base=[t['start']-.5 for t in subset], orientation='h', name=track, marker_color=palette[i], customdata=[[t['label'],t['start'],t['end']] for t in subset], hovertemplate='%{customdata[0]}<br>%{customdata[1]}–%{customdata[2]} aa<extra></extra>'))
        fig.update_layout(barmode='overlay', height=330, xaxis_title='Residue position · 1-based, inclusive', showlegend=False)
        chart(fig)
        st.caption('Overlapping features can overlap visually; inspect the tables for all hits. CDD track displays specific hits only. Topology states are the original DeepTMHMM codes (I/O/M/S).')
    else:
        st.info('No positional annotations available for this protein.')
    tabs = st.tabs(['Annotations', 'Motifs', 'Prediction evidence', 'Sequence & provenance'])
    with tabs[0]:
        table(records.T.reset_index().rename(columns={'index':'field'}).astype(str))
    with tabs[1]:
        st.caption('Regex motif candidates are not validated binding sites. Review context_state and review_note before interpretation.')
        table(local_hits)
    with tabs[2]:
        for name, evidence in raw.items():
            matched = evidence[evidence.sequence_id.eq(key)]
            if not matched.empty:
                with st.expander(name):
                    table(matched)
    with tabs[3]:
        table(memberships[memberships.sequence_id.eq(key)])
        if seq:
            st.code('\n'.join(seq[i:i+80] for i in range(0,len(seq),80)), language=None)
            st.download_button('↓ Protein FASTA', fasta_export([key], sequences), key+'.fasta')
        else:
            st.warning('No source FASTA sequence found.')

elif page == 'Comparative lab':
    st.subheader('Comparative lab')
    st.caption('Representation within the selected candidate collection; not proteome-normalized abundance, expression, enrichment or orthology.')
    mode = st.radio('Heatmap units', ['Distinct proteins', '% of filtered species proteins'], horizontal=True)
    matrix = df.groupby(['family','species']).sequence_id.nunique().unstack(fill_value=0)
    if mode.startswith('%'):
        matrix = matrix.div(df.groupby('species').sequence_id.nunique(), axis=1)*100
    chart(px.imshow(matrix, text_auto='.1f' if mode.startswith('%') else True, aspect='auto', color_continuous_scale='Teal', labels=dict(color=mode), title='Family repertoire by species', height=max(430,len(matrix)*24)))
    download(matrix.reset_index(), 'species_family_matrix.csv')
    chart(px.box(df, x='family', y='length', color='species', points='outliers', color_discrete_sequence=palette, title='Protein length distributions · hypothesis records', labels={'length':'Length (aa)'}))
    selected = st.multiselect('Compare protein annotations (up to 6)', sorted(ids), max_selections=6)
    if selected:
        table(df[df.sequence_id.isin(selected)])
    coverage_cols = [c for c in ['architecture','NCBI_CDD_architecture','DeepLoc_2.1','DeepTMHMM','SignalP.v6.0'] if c in df]
    coverage = pd.DataFrame([{'species':species_name,'evidence':col,'coverage (%)':group.loc[group[col].notna(),'sequence_id'].nunique()/group.sequence_id.nunique()*100} for species_name,group in df.groupby('species') for col in coverage_cols])
    chart(px.bar(coverage,x='evidence',y='coverage (%)',color='species',barmode='group',color_discrete_sequence=palette,title='Annotation availability · not evidence strength'))

elif page == 'Motif explorer':
    st.subheader('Motif explorer')
    st.info('These are sequence-pattern hypotheses. Motif counts do not establish interactions. Context and source review notes accompany every hit.')
    if hits.empty:
        st.info('No reported motif hits for the selected proteins.')
    else:
        classes = st.multiselect('ELM classes', sorted(hits.elm_class.unique()))
        context = st.multiselect('Context states', sorted(hits.context_state.dropna().unique()))
        if classes:
            hits = hits[hits.elm_class.isin(classes)]
        if context:
            hits = hits[hits.context_state.isin(context)]
        if not hits.empty:
            summary = hits.groupby(['elm_class','context_state']).size().reset_index(name='hits')
            chart(px.bar(summary,x='hits',y='elm_class',color='context_state',color_discrete_sequence=palette,title='Motif candidates and their sequence context'))
        table(hits)
        download(hits, 'motif_candidates.csv')

elif page == 'Citations':
    bibliography = (ROOT / 'CITATIONS.md').read_text(encoding='utf-8')
    st.markdown(bibliography)
    st.download_button('Download bibliography · Markdown', bibliography, 'Schisto_Adhesome_Atlas_citations.md', 'text/markdown')

elif page == 'Source Library':
    st.subheader('Source library & data audit')
    st.caption('All files beneath adhesome_atlas are indexed here. This view is independent of candidate filters. Original files are read only.')
    files = source_files()
    inventory = pd.DataFrame([{'file':p.relative_to(ROOT).as_posix(), 'format':p.suffix, 'bytes':p.stat().st_size} for p in files])
    table(inventory)
    chosen = st.selectbox('Open a source', inventory.file)
    path = ROOT / chosen
    st.download_button('↓ Download original source', path.read_bytes(), path.name)
    if chosen in books:
        sheet = st.selectbox('Worksheet', list(books[chosen]))
        table(books[chosen][sheet])
    elif path.suffix in ['.tsv','.all']:
        table(pd.read_csv(path, sep='\t'))
    elif path.name in raw:
        table(raw[path.name])
    elif path.suffix == '.fasta':
        table(memberships[memberships.source.eq(chosen)])
        st.code(path.read_text()[:6000], language=None)
        st.caption('Text preview limited to 6,000 characters; download contains the complete source.')
    else:
        st.code(path.read_text(errors='replace')[:12000],language=None)
    st.markdown('### Reconciliation checks')
    audit=[]
    for label, frame in cohorts.items():
        unique=frame.drop_duplicates('sequence_id')
        audit.append({'collection':label, 'records':len(frame),'distinct proteins':len(unique),'without FASTA':sum(key not in sequences for key in unique.sequence_id),'length mismatches':sum(key in sequences and pd.notna(length) and len(sequences[key]) != int(length) for key,length in zip(unique.sequence_id,unique.length))})
    table(pd.DataFrame(audit))
    st.write(f'Sequence conflicts across FASTA sources: {len(conflicts)}')
    if conflicts:
        table(pd.DataFrame(conflicts))
    st.markdown('**Interpretation:** Screening rows represent protein–family hypotheses. FN3 review assignments are retained separately from the original fibronectin-like screening label. Missing evidence means unavailable in this collection. Family FASTAs supply membership and sequence provenance; they are not added as extra candidate records. Network edges come only from the supplied STRING interaction exports; no additional interactions are inferred.')

st.divider()
with st.expander('Resource citations and acknowledgements'):
    st.markdown('Networks: [STRING](https://version-12-5.string-db.org/) · Motifs: [ELM](http://elm.eu.org/) · Protein references: [UniProt](https://www.uniprot.org/) · Domains: [InterPro](https://www.ebi.ac.uk/interpro/) and [NCBI CDD](https://www.ncbi.nlm.nih.gov/Structure/cdd/cdd.shtml) · Predictions: [SignalP 6.0](https://services.healthtech.dtu.dk/services/SignalP-6.0/), [DeepLoc 2.1](https://services.healthtech.dtu.dk/services/DeepLoc-2.1/), [DeepTMHMM](https://services.healthtech.dtu.dk/services/DeepTMHMM-1.0/) · Genomes: [WormBase ParaSite](https://parasite.wormbase.org/).')
    st.caption('Open Citations in the sidebar for publication references and the downloadable bibliography.')
st.caption('SCHISTO-ADHESOME ATLAS  /  Local annotation atlas  /  Source: adhesome_atlas  /  Predictions remain hypotheses')
creator_credit()
