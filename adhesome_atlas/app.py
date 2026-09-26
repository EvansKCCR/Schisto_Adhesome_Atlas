from pathlib import Path
from urllib.parse import urlencode, quote
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
from orthology_explorer import orthology_panel
from phylogeny_view import phylogeny_panel
from branding import identity_banner, creator_credit

st.set_page_config(page_title='Schisto-Adhesome Atlas | Integrin–adhesome', page_icon='🧬', layout='wide')
st.markdown("""<style>
.block-container{padding-top:2rem;max-width:1500px;padding-bottom:3rem}
[data-testid="stAppViewContainer"]{background:#fff}
[data-testid="stAppViewContainer"] p,[data-testid="stAppViewContainer"] li{font-size:1.05rem;line-height:1.65;color:#171717}
h1,h2,h3{letter-spacing:-.025em;color:#111;font-weight:750}
h2{font-size:1.85rem}h3{font-size:1.5rem}
.hero{background:#064c2c;color:white;padding:38px 42px;border-radius:18px;margin-bottom:24px;border-bottom:6px solid #f4cf24}
.hero h1{color:#fff;font-size:clamp(2.2rem,3.6vw,3.3rem);line-height:1.15;margin:12px 0 18px;letter-spacing:-.035em;font-weight:800}
[data-testid="stAppViewContainer"] .hero p{color:#fff;max-width:850px;font-size:1.15rem;line-height:1.65;margin-bottom:0}
.eyebrow{font-size:.85rem;letter-spacing:2px;text-transform:uppercase;color:#ffe34d;font-weight:750}
[data-testid="stMetric"]{background:#fff;border:1px solid #b6c5ba;border-top:4px solid #08743f;border-radius:12px;padding:20px}
[data-testid="stMetricValue"]{color:#064c2c;font-size:2.3rem;font-weight:750}
[data-testid="stMetricLabel"] p{color:#111!important;font-weight:650}
[data-testid="stSidebar"]{background:#f4f6f2;border-right:2px solid #c7d1c6}
[data-testid="stSidebar"] h2{font-size:1.4rem;line-height:1.35;color:#064c2c}
[data-testid="stSidebar"] [role="radiogroup"]{gap:5px}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:8px;padding:7px 10px}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#e2ebdf}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#ffe34d;box-shadow:inset 4px 0 #064c2c}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:#111;font-weight:750}
[data-testid="stWidgetLabel"] p{color:#171717!important;font-size:1rem!important;font-weight:650}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button{background:#fff;color:#064c2c;border:1.5px solid #08743f;border-radius:8px;font-weight:650}
[data-testid="stButton"] button p,[data-testid="stDownloadButton"] button p{color:inherit}
[data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover{background:#ffe34d;color:#111;border-color:#111}
button:focus-visible,a:focus-visible{outline:3px solid #b91c1c!important;outline-offset:3px}
[data-testid="stDataFrame"],[data-testid="stPlotlyChart"]{border:1px solid #bac8bc;border-radius:12px;background:#fff;padding:6px}
[data-testid="stExpander"]{border-radius:10px;background:#fff;border-color:#bac8bc}
[data-testid="stTabs"] [role="tablist"]{gap:12px;border-bottom:2px solid #ccd4cb}
[data-testid="stTabs"] [role="tab"]{padding:10px 12px;border-radius:8px 8px 0 0;color:#111}
[data-testid="stTabs"] [aria-selected="true"]{background:#ffe34d;color:#111;font-weight:750}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{background:#b91c1c}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:#333!important;font-size:.95rem!important;line-height:1.6}
[data-testid="stMarkdownContainer"] a{color:#075d32;text-decoration:underline;text-underline-offset:3px;font-weight:600}
[data-testid="stMarkdownContainer"] a:hover{color:#b91c1c}
@media(max-width:640px){.hero{padding:26px 22px}.eyebrow{letter-spacing:1px}.block-container{padding-top:1.2rem}[data-testid="stMetric"]{padding:14px}}
</style>""", unsafe_allow_html=True)

@st.cache_data(show_spinner='Reading annotation and evidence library…')
def cached_data(signature):
    return load()

try:
    cohorts, books, motifs, sequences, memberships, raw, topologies, conflicts = cached_data(fingerprint())
except Exception as exc:
    st.error(f'Unable to read annotation library at {ROOT}: {exc}')
    st.stop()

# Cloud deployments can retain cached cohorts from an older data loader while
# serving a newer app.py. Normalize that schema before any page uses it.
def ensure_audit_columns(frame):
    if {'audit_classification','reviewed_family','family_assignment_basis'} <= set(frame.columns):
        return frame
    out = frame.copy()
    if 'family_decision' in out:
        supported = {'Retain family assignment','Retain; resolves competing family'}
        provisional = {'Retain provisionally','Family-level provisional only'}
        decisions = out.family_decision.fillna('')
        out['audit_classification'] = decisions.map(
            lambda decision: 'Supported' if decision in supported else
            'Provisional' if decision in provisional else
            'Ambiguous' if decision.startswith('Ambiguous') else 'Unassigned'
        )
        out['reviewed_family'] = out.family.where(out.audit_classification.isin(['Supported','Provisional']))
        out['family_assignment_basis'] = decisions
    elif {'recommended_family','grade'} <= set(out.columns):
        out['audit_classification'] = out.grade.map({'A':'Supported','B':'Supported','C':'Provisional','D':'Unassigned'}).fillna('Unassigned')
        out['reviewed_family'] = out.recommended_family.where(out.audit_classification.ne('Unassigned'))
        out['family_assignment_basis'] = out.rationale if 'rationale' in out else 'Workbook recommended family and grade'
    else:
        out['audit_classification'] = 'Screening hypothesis'
        out['reviewed_family'] = pd.NA
        out['family_assignment_basis'] = 'Audited workbook columns are unavailable in this deployment'
    return out

cohorts = {name: ensure_audit_columns(frame) for name, frame in cohorts.items()}
missing_audit_sources = [name for name, required in [('Adhesome candidates','family_decision'),('FN3 / fibronectin-like review','recommended_family')]
                         if required not in cohorts[name]]

with st.sidebar:
    st.markdown('## 🧬 Schisto-Adhesome Atlas')
    st.caption('INTEGRIN · ADHESOME · EVIDENCE')
    section = st.radio('Explore', ['Introduction', 'Components', 'Interactions', 'Orthology', 'Phylogeny', 'Protein dossier', 'Motif explorer', 'Comments & feedback', 'Source Library', 'Citations'])
    page = section
    if section == 'Components':
        page = st.radio('Component view', ['Summary statistics', 'Summary graphs', 'Candidate catalogue', 'Family assignment audit', 'Comparative lab', 'Orthology & evidence', 'FN3 / RPTP priorities'])
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
palette = ['#127f83', '#cb7836', '#7563ac', '#39876c', '#b34f78', '#527b9b']

def chart(fig):
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#171717',size=15), margin=dict(l=12,r=12,t=45,b=20), colorway=palette)
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
st.markdown('<div class="hero"><div class="eyebrow">Comparative molecular atlas · Schistosoma</div><h1>Schisto-Adhesome Atlas</h1><p>Explore integrin–adhesome candidates across three schistosome species, from family assignments to domains, sequence motifs and localization evidence.</p></div>', unsafe_allow_html=True)
if missing_audit_sources:
    st.warning('Audited workbook columns are unavailable for '+', '.join(missing_audit_sources)+'. Deploy the updated files/ workbooks together with app.py, data.py and family_audit.py, then use Reload source files.')
st.caption(f'{cohort}  /  {len(df):,} filtered assignment records  /  {df.sequence_id.nunique():,} distinct proteins')

if page not in ['Source Library', 'Interactions', 'Introduction', 'Citations', 'FN3 / RPTP priorities', 'Phylogeny', 'Orthology'] and df.empty:
    st.info('No candidates match these filters. Select a species or broaden your search.')
    st.stop()

if page == 'Introduction':
    st.subheader('About the Schisto-Adhesome Atlas')
    st.markdown('The **Schisto-Adhesome Atlas** is an interactive platform for exploring adhesion-associated proteins across medically important *Schistosoma* species. It integrates protein annotations, orthology, phylogeny, conserved domains and motif exploration to reveal evolutionary relationships, parasite-specific features and potential functional interaction modules. By connecting comparative bioinformatics with experimental prioritization, the Atlas supports the discovery of candidate drug targets, vaccine antigens and biomarkers for schistosomiasis research.')
    st.caption('Collection totals below describe all records in each source collection. The filtered selection is shown above.')
    for col, label, frame in zip(st.columns(3), cohorts.keys(), cohorts.values()):
        col.metric(label, f'{frame.sequence_id.nunique():,} proteins', f'{len(frame):,} assignment records', delta_color='off')
    st.subheader('Prototype schistosome integrin adhesome')
    prototype = ROOT / 'Prototype_schistosome_integrin_adhesome.png'
    if prototype.is_file():
        st.image(str(prototype), caption='Prototype schistosome integrin adhesome', width='stretch')
    else:
        st.info('Prototype image unavailable. Include Prototype_schistosome_integrin_adhesome.png alongside app.py.')

elif page == 'Orthology':
    orthology_panel(network_candidates)

elif page == 'Phylogeny':
    phylogeny_panel(network_candidates)

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
    st.markdown('### Audited family assignments')
    classification = df.groupby(['species','audit_classification']).agg(assignment_records=('sequence_id','size'),distinct_proteins=('sequence_id','nunique')).reset_index()
    table(classification)
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
    st.info('Counts are distinct proteins within each plotted group. Multiple family assignments can make group totals exceed the collection’s distinct-protein count. Original source statuses are retained.')
    st.markdown('### Family assignment audit')
    classification = df.groupby(['family','audit_classification']).size().reset_index(name='assignment records')
    chart(px.bar(classification,x='family',y='assignment records',color='audit_classification',barmode='stack',title='Family screening labels by audited classification'))
    st.markdown('### Follow the evidence')
    for col, title, body in zip(st.columns(3), ['01 / Find a candidate', '02 / Inspect its architecture', '03 / Compare the repertoire'], ['Search identifiers, families and Pfam annotations in the catalogue.', 'Open a dossier for positional domains, motifs, topology and raw predictor results.', 'Compare species using absolute counts or within-species family representation.']):
        with col:
            st.markdown(f'**{title}**')
            st.write(body)

elif page == 'Candidate catalogue':
    st.subheader('Candidate catalogue')
    defaults = [c for c in ['sequence_id','species','family','reviewed_family','audit_classification','grade','family_decision','module','status','length','architecture','DeepLoc_2.1','orthogroup','evidence_review_stage','priority_group'] if c in df]
    columns = st.multiselect('Visible annotation fields', list(df.columns), default=defaults)
    table(df[columns])
    a,b = st.columns(2)
    with a:
        download(df, 'filtered_candidates.csv')
    with b:
        st.download_button('↓ Filtered proteins · FASTA', fasta_export(df.sequence_id, sequences), 'filtered_proteins.fasta', 'text/plain')
    st.caption(f'{len(ids.intersection(sequences)):,} of {len(ids):,} filtered proteins have a source sequence. FASTA exports deduplicate protein IDs; CSV retains each hypothesis.')

elif page == 'Family assignment audit':
    st.subheader('Conservative family assignment audit')
    st.caption('The screening family remains visible. Reviewed family follows the audited decision; domain architecture is the primary gate, with orthology, motif context and localization as supporting evidence. Experimental validation is downstream and was not used in the audit.')
    grades = [c for c in ['grade','family_decision','recommended_family'] if c in df]
    if not grades:
        st.info('This source collection has no family-assignment audit. Choose Adhesome candidates or FN3 / fibronectin-like review.')
    else:
        classes = st.multiselect('Audited classification',sorted(df.audit_classification.dropna().unique()))
        reviewed = df[df.audit_classification.isin(classes)] if classes else df
        a,b,c,d = st.columns(4)
        for col,label in zip([a,b,c,d],['Supported','Provisional','Ambiguous','Unassigned']):
            col.metric(label,f'{reviewed.audit_classification.eq(label).sum():,} records')
        count = reviewed.groupby(['family','audit_classification']).size().reset_index(name='records')
        if not count.empty:
            chart(px.bar(count,x='family',y='records',color='audit_classification',barmode='stack',title='Audited decisions by screening family'))
        cols=[c for c in ['sequence_id','species','family','assigned_family','recommended_family','reviewed_family','audit_classification','grade','family_decision','FN1_count','FN2_count','FN3_count','domain_match','domain_type_fraction','domain_copy_fraction','domain_score_0_4','orthology_score_0_3','motif_score_0_2','motif_score_0_1','localization_score_0_1','total_score_0_10','rationale','competing_supported_families'] if c in reviewed]
        table(reviewed[cols])
        download(reviewed,'audited_family_assignments.csv')
        if cohort=='Adhesome candidates':
            conflicts=books['files/adhesome_candidates_list.xlsx'].get('Multi_family_conflicts')
            if conflicts is not None:
                with st.expander(f'Competing family labels · {len(conflicts)} proteins'):
                    table(conflicts)
            with st.expander('Audit rules and per-family summary'):
                for sheet in ['Family_assignment_rule','Family_Audit']:
                    st.markdown(f'**{sheet.replace("_"," ")}**')
                    table(books['files/adhesome_candidates_list.xlsx'][sheet])
        elif cohort=='FN3 / fibronectin-like review':
            st.info('No reviewed protein meets the strict canonical fibronectin architecture. The workbook assigns specific FN3-containing receptor, secreted, intracellular and other protein classes.')
            with st.expander('FN3 family assignment rules'):
                table(books['files/fibronectin_like_candidate.xlsx']['Family_assignment_rule'])

elif page == 'Protein dossier':
    key = st.selectbox('Protein', sorted(ids))
    records = df[df.sequence_id.eq(key)]
    row = records.iloc[0]
    st.subheader(key)
    st.write(f"{row.species} · {' / '.join(records.family.unique())}")
    seq = sequences.get(key, '')
    a,b,c = st.columns(3)
    a.metric('Sequence length', f'{len(seq):,} aa' if seq else 'Unavailable')
    b.metric('Family assignments in selection', len(records))
    local_hits = motifs[motifs.sequence_id.eq(key)]
    c.metric('Reported motif hits', len(local_hits))
    tracks = []
    for architecture in records.architecture.dropna().unique():
        tracks.extend([dict(track='Pfam', label=n, start=s, end=e) for n,s,e in intervals(architecture)])
    for name, evidence in raw.items():
        if 'CDD' in name:
            for _, r in evidence[evidence.sequence_id.eq(key) & evidence['Hit type'].eq('specific')].iterrows():
                tracks.append(dict(track='CDD · specific', label=r['Short name'], start=r['From'], end=r['To']))
    tracks.extend(dict(track='Motif · predicted',label=r.motif_label,start=r.start,end=r.end) for r in local_hits.itertuples())
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
        st.caption('Motif annotations include candidate tiers, supported and conflicting criteria, functional assignments, partners and primary references. Library confidence and candidate context are shown separately.')
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
    st.info('Motif hits are shown with sequence position, domain/topology context and source annotations to support integrated interpretation.')
    if hits.empty:
        st.info('No reported motif hits for the selected proteins.')
    else:
        classes = st.multiselect('Motif IDs and names', sorted(hits.motif_label.unique()))
        context = st.multiselect('Candidate assignment tiers', sorted(hits.candidate_tier.dropna().unique()))
        if classes:
            hits = hits[hits.motif_label.isin(classes)]
        if context:
            hits = hits[hits.candidate_tier.isin(context)]
        if not hits.empty:
            summary = hits.groupby(['motif_label','candidate_tier']).size().reset_index(name='hits')
            chart(px.bar(summary,x='hits',y='motif_label',color='candidate_tier',color_discrete_sequence=palette,title='Motif annotations by candidate assignment tier'))
        table(hits)
        download(hits, 'motif_candidates.csv')

elif page == 'Comments & feedback':
    st.subheader('Comments & feedback')
    st.write('Share a catalogue correction, interpretation, suggestion, or question with the Atlas curator. Include a protein accession, orthogroup, or source file when relevant.')
    with st.form('atlas_feedback_form'):
        kind = st.selectbox('Message type', ['Comment or correction', 'Feedback or suggestion', 'Scientific query'])
        subject_detail = st.text_input('Protein, orthogroup, or topic (optional)', max_chars=120)
        sender = st.text_input('Your name (optional)', max_chars=100)
        reply_to = st.text_input('Your email for a reply (optional)', max_chars=200)
        message = st.text_area('Your message', max_chars=2000, height=170)
        prepare = st.form_submit_button('Prepare email draft')
    if prepare:
        if not message.strip():
            st.error('Enter a comment, suggestion, or question to prepare the email draft.')
        else:
            subject = 'Schisto-Adhesome Atlas · ' + kind
            if subject_detail.strip():
                subject += ' · ' + subject_detail.strip()
            body = '\n'.join([
                f'Message type: {kind}',
                f'Topic: {subject_detail.strip() or "Not specified"}',
                f'Name: {sender.strip() or "Not provided"}',
                f'Reply email: {reply_to.strip() or "Not provided"}',
                '', message.strip(),
            ])
            mailto = 'mailto:evansasamoahadu@gmail.com?' + urlencode({'subject': subject, 'body': body}, quote_via=quote)
            st.success('Your draft is ready. Open it in your email app, review it, and send it.')
            st.markdown(f'[Open email draft addressed to evansasamoahadu@gmail.com]({mailto})')
    st.markdown('### Direct queries')
    st.markdown('For scientific queries or correspondence, email [evansasamoahadu@gmail.com](mailto:evansasamoahadu@gmail.com).')
    st.caption('The Atlas does not store or send form entries. The email draft opens in your own mail app.')

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
st.caption('SCHISTO-ADHESOME ATLAS  /  Local annotation atlas  /  Source: adhesome_atlas  /  Assignments integrate complementary evidence')
creator_credit()
