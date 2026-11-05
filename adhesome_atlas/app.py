"""Multi-species Schisto-Adhesome Atlas entry point."""
from pathlib import Path
from decimal import Decimal
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import json
import time
from zipfile import BadZipFile
import pandas as pd
import plotly.express as px
import streamlit as st
from atlas_styles import apply_style,introduction_hero
from data import ROOT,SCHEMA_VERSION,load,fingerprint,source_files,fasta_export,family_audit_table,annotate_motif_sites
from figure_exports import plotly_chart,figure_download_settings
from curated_network import consensus_panel
from orthology_explorer import orthology_panel
from phylogeny_view import phylogeny_panel
from string_workbench import string_panel
from smart_links import smart_panel
from linked_explorer import linked_explorer_html
from simulator import simulator_html,SIMULATOR_FILE
from feedback import feedback_panel
from branding import identity_banner,creator_credit
from candidate_profiles import profile_payload,candidate_map_html,atlas_url
from research_priorities import apply_target_route,research_priorities_panel
from library_refresh import refresh_family_html
from source_watch import reconcile_selections,watch_sources
from reclassification import FILE as RECLASS_FILE,SHEET as RECLASS_SHEET,MAP_LABEL,classification_view
from reclassification_view import reclassification_panel,map_url
from functional_categories_view import functional_category_panel
from navigation import PAGES,HYPOTHESIS_PAGE,hypothesis_url
apply_style()

@st.cache_data(show_spinner='Reading current annotation library…',max_entries=3)
def cached_data(signature,schema_version):return load()
loaded_signature=fingerprint()
try:
    cohorts,books,motifs,sequences,memberships,raw,topologies,conflicts=cached_data(loaded_signature,SCHEMA_VERSION)
except (OSError,ValueError,KeyError,BadZipFile) as error:
    st.warning('Waiting for a complete, readable source library: '+str(error))
    retry_at=st.session_state.setdefault('atlas_source_retry_at',time.monotonic()+30)
    @st.fragment(run_every='30s')
    def retry_sources():
        if time.monotonic()>=retry_at:
            st.session_state.pop('atlas_source_retry_at',None);st.rerun()
        st.caption('Finish saving or uploading the source files. The Atlas will retry automatically in 30 seconds.')
    retry_sources();st.stop()
st.session_state.pop('atlas_source_retry_at',None)
all_candidates=cohorts['Adhesome candidates']
from scientific_text import register_species,install_browser_typography
if register_species(all_candidates.species.dropna().unique()):install_browser_typography()
reconcile_selections(st.session_state,all_candidates)
requested_protein=st.query_params.get('protein','')
requested_view=st.query_params.get('view','')
apply_target_route(all_candidates,st.query_params,st.session_state)
app_url=st.context.url or ''

@st.cache_data(show_spinner='Connecting candidate evidence profiles…',max_entries=3)
def cached_profiles(signature,_candidates,_books,_motifs):
    return profile_payload(_candidates,_books,_motifs)


def table(frame):
    shown=frame.copy()
    evalues={c for c in shown if str(c).lower().replace('-','').replace('_','').replace(' ','')=='evalue'}
    for c in shown:
        if c in evalues:shown[c]=pd.to_numeric(shown[c],errors='coerce')
        elif shown[c].dtype==object: shown[c]=shown[c].fillna('').astype(str)
    st.dataframe(shown,hide_index=True,width='stretch',column_config={
        c:st.column_config.NumberColumn('E-value',format='scientific') for c in evalues})

def download(frame,name,label='Download table CSV'):
    st.download_button(label,frame.to_csv(index=False),name,'text/csv')

def motif_view(sites,key='motifs'):
    st.subheader('Motif context evidence')
    sites=annotate_motif_sites(sites,all_candidates)
    repeated=sites.attrs['motif_annotation_summary']['repeated_protein_ids']
    if repeated:st.caption(f'{len(repeated)} protein ID(s) have multiple catalogue records. Distinct annotation labels are combined here; each motif site is retained once.')
    a,b=st.columns(2)
    names=a.multiselect('Motif function',sorted(sites.motif_function.dropna().unique()),key=key+'_function')
    tiers=b.multiselect('Motif context tier',sorted(sites.reassessed_context_tier.dropna().unique()),key=key+'_tier')
    if names:sites=sites[sites.motif_function.isin(names)]
    if tiers:sites=sites[sites.reassessed_context_tier.isin(tiers)]
    st.caption('Positional motif predictions use Motif_annotations.xlsx. Context tiers, peptides, ELM classes, overlapping domains and topology are retained for each site.')
    for col,label,value in zip(st.columns(3),['Motif sites','Proteins','Functions'],[len(sites),sites.sequence_id.nunique(),sites.motif_function.nunique()]):col.metric(label,value)
    if len(sites):
        counts=sites.groupby(['motif_function','reassessed_context_tier']).size().reset_index(name='Sites')
        plotly_chart(px.bar(counts,x='motif_function',y='Sites',color='reassessed_context_tier'),width='stretch')
    table(sites);download(sites,key+'_sites.csv')

with st.sidebar:
    st.markdown('<div class="atlas-sidebar-brand"><span class="atlas-sidebar-symbol" aria-hidden="true">αβ</span><div><strong>Schisto-Adhesome<br>Atlas</strong></div></div>',unsafe_allow_html=True)
    page=st.radio('Explore',PAGES,key='atlas_page')
    st.divider()
    st.caption('REFINE THE CATALOGUE')
    species_options=sorted(all_candidates.species.unique())
    st.session_state.setdefault('catalogue_species',species_options)
    species=st.multiselect('Species',species_options,key='catalogue_species')
    families=st.multiselect('Protein families',sorted(all_candidates.family.unique()),key='catalogue_families')
    classification=st.selectbox('Classification',['All','Supported','Provisional','Unassigned'],key='catalogue_classification')
    query=st.text_input('Search annotations',key='catalogue_query')
    figure_download_settings()
    auto_refresh=st.toggle('Automatically update inventory',value=True,key='atlas_auto_refresh',
        help='Checks deployed source files every 30 seconds, including candidate workbook content changes. Updates inventory, counts, profiles and derived networks. Turn off to pause background checks; opening/reloading the Atlas still reads current files.')
    if st.button('Reload source files'):st.cache_data.clear();st.rerun()
    watch_sources(loaded_signature,enabled=auto_refresh)
    if all_candidates.attrs.get('library_storage_error'):st.caption('Derived files are refreshed in memory; disk mirrors could not be saved on this host.')
    st.caption(f'{len(all_candidates):,} assignment records · {all_candidates.sequence_id.nunique():,} proteins · {all_candidates.species.nunique()} species · {all_candidates.family.nunique()} family labels')
selected=all_candidates[all_candidates.species.isin(species)].copy()
if families:selected=selected[selected.family.isin(families)]
if classification!='All':selected=selected[selected.audit_classification.eq(classification)]
if query:selected=selected[selected.fillna('').astype(str).apply(lambda s:s.str.contains(query,case=False,regex=False)).any(axis=1)]

if page=='Introduction':
    identity_banner()
    introduction_hero(all_candidates,app_url)
    entry_columns=st.columns(2)
    for column,(title,filename) in zip(entry_columns,[
        ('Read more: Schistosome adhesome interactor','README_schistosome_adhesome_interactive.md'),
        ('Read more: Schistosome adhesome simulator','README_adhesome_hypothesis_simulator.md'),
    ]):
        with column.expander(title,expanded=False):
            readme=ROOT/filename
            if readme.exists():st.markdown(readme.read_text(encoding='utf-8'))
            else:st.info('To be updated when additional information is available.')
    @st.fragment
    def research_entry():
        research_priorities_panel(all_candidates,app_url,ROOT/'Target_prioritization.md')
    research_entry()

elif page==HYPOTHESIS_PAGE:
    st.header('Interactive integrin-adhesome hypothesis')
    st.caption('Explore candidate families, their recorded connections and evidence profiles, then inspect the linked downstream simulation.')
    labels=all_candidates.set_index('sequence_id').display_annotation.to_dict()
    choices=['']+sorted(set(all_candidates.sequence_id))
    with st.expander('Locate a candidate by accession',expanded=False):
        focus=st.selectbox('Locate a candidate on the map',choices,key='map_candidate',
            format_func=lambda key:'Browse families and candidate profiles' if not key else key+' · '+labels[key])
    st.markdown('<span id="hypothesis-workspace"></span>',unsafe_allow_html=True)
    network_dir=ROOT/'adhesome_network'
    basis=st.selectbox('Hypothesis map grouping',['Catalogue families',MAP_LABEL],key='atlas_map_basis',
        help='The Pfam–CDD view groups recovered family and domain hypotheses by their classification. Original catalogue grades/support remain explicit; domain classes do not create reference interactions.')
    map_candidates=classification_view(all_candidates) if basis==MAP_LABEL else all_candidates
    if basis==MAP_LABEL:st.caption('Pfam–CDD A/B/C classes provide browsing groups and functional context. Their evidence tiers are separate from catalogue grades. Reference edges still use supported catalogue identities in shared species.')
    path=next((network_dir/name for name in ['Schistosome_adhesome_interactive.html','Schistosome_adhesome_rebuilt.html'] if (network_dir/name).exists()),None)
    if path:
        html=refresh_family_html(path.read_text(encoding='utf-8'),map_candidates,ROOT).replace('previously supplied model','adhesome model in the library')
        profiles=cached_profiles((fingerprint(),SCHEMA_VERSION,basis),map_candidates,books,motifs)
        html=candidate_map_html(html,profiles,app_url=app_url,focus_candidate=focus)
        html=html.replace('</head>','<style>svg text{fill:#000!important;font-family:Arial,sans-serif}</style></head>')
        sim=ROOT/SIMULATOR_FILE
        if sim.exists():html=linked_explorer_html(html,simulator_html(sim,all_candidates))
        st.iframe(html,height=980)
        st.download_button('Download interactive map and linked simulator',html,'Schisto_Adhesome_interactive.html','text/html')
        st.caption('Click any node to explore its linked candidates, then simulate the selected candidate and highlighted path. The profile remains visible beside the simulation; the search box is optional. Simulator weights are conceptual parameters; metazoan reference evidence counts are not used as binding affinities.')
    else:st.info('No interactive map is present in the current network library.')
    st.subheader('Build an evidence-stratified schistosome adhesome hypothesis')
    st.write('Use Interactions to choose species, grades and families, construct the orthogroup consensus graph, and download membership, reference-edge evidence, centrality and provenance.')

elif page=='Components':
    st.header('Components')
    st.caption('Choose a section below. Species, family and classification filters remain in the sidebar.')
    requested_family=st.query_params.get('family','')
    if requested_view=='Components' and requested_family and requested_family not in set(all_candidates.family):
        st.info('The requested family is unavailable in the current catalogue: '+requested_family)
    view=st.selectbox('Component section',['Summary statistics','Summary graphs','Supported families by functional category','Pfam–CDD family reclassification','Candidate catalogue','Family assignment audit','Comparative lab','Candidate prioritization'],key='component_section')
    if view=='Pfam–CDD family reclassification':reclassification_panel(selected,books.get(RECLASS_FILE,{}).get(RECLASS_SHEET),app_url,library_candidates=all_candidates)
    elif view=='Supported families by functional category':functional_category_panel(selected)
    elif view in ['Summary statistics','Summary graphs','Comparative lab']:
        counts=selected.groupby(['species','family']).sequence_id.nunique().reset_index(name='Proteins')
        if view=='Summary statistics':
            table(selected.groupby(['species','grade','assignment_confidence']).size().reset_index(name='Candidates'))
            counts=selected.drop_duplicates('sequence_id').reclassification_tier.value_counts()
            st.caption('Local Pfam–CDD reclassification: '+', '.join(t+' = '+str(int(counts.get(t,0))) for t in ['A','B','C','D'])+'. Explore family hypotheses and complete evidence in the Pfam–CDD family reclassification section.')
        elif view=='Summary graphs':
            if len(counts):plotly_chart(px.bar(counts,x='family',y='Proteins',color='species'),width='stretch')
            if len(selected):plotly_chart(px.treemap(selected.groupby(['module','family']).size().reset_index(name='Proteins'),path=['module','family'],values='Proteins',color='module'),width='stretch')
        else:
            matrix=counts.pivot(index='family',columns='species',values='Proteins').fillna(0)
            if len(matrix):plotly_chart(px.imshow(matrix,aspect='auto',height=max(500,len(matrix)*23),title='Family repertoire across species'),width='stretch')
            download(matrix.reset_index(),'family_species_counts.csv')
    elif view=='Candidate prioritization':
        st.write('Rank candidates using the current audited evidence scores. Orthology benchmark weights and family confidence are retained. Scores are separate from reference-network centrality; domain architecture, topology and motif context remain explicit supporting evidence.')
        metric=st.selectbox('Rank by',['total_score_0_10','domain_score_0_4','orthology_score_0_3','motif_score_0_2','localization_score_0_1','Local Pfam–CDD priority / tier'])
        if metric=='Local Pfam–CDD priority / tier':
            from reclassification import priority_order
            ranked=priority_order(selected)
            st.caption('Unique proteins ordered by the reported P1–P4 priority, then Pfam–CDD evidence tier. Catalogue scores remain available as separate columns.')
        else:ranked=selected.sort_values(metric,ascending=False).reset_index(drop=True)
        ranked.insert(0,'rank',range(1,len(ranked)+1))
        table(ranked);download(ranked,'candidate_prioritization.csv')
    elif view=='Family assignment audit':
        audit,missing=family_audit_table(selected)
        if missing:st.caption('No additional information present in the current library for: '+', '.join(missing)+'.')
        table(audit);download(selected,'family_assignment_audit.csv')
    else:table(selected);download(selected,'candidate_catalogue.csv')

elif page=='Interactions':
    st.header('Interactions')
    st.caption('Choose a network workspace, then select the visualization, centrality, clustering or evidence section. Each section uses the full page width.')
    workspace=st.selectbox('Network workspace',['Curated orthogroup consensus','STRING query & import'])
    if workspace=='Curated orthogroup consensus':consensus_panel(all_candidates)
    else:string_panel(all_candidates,sequences)

elif page=='Orthology':orthology_panel(all_candidates)
elif page=='Phylogeny':
    @st.fragment(run_every='30s')
    def live_phylogeny():phylogeny_panel(all_candidates,app_url)
    live_phylogeny()

elif page=='Motif explorer':motif_view(motifs[motifs.sequence_id.isin(selected.sequence_id)])
elif page=='Protein dossier':
    st.header('Protein dossier')
    if selected.empty and requested_protein not in set(all_candidates.sequence_id):st.info('No proteins match the catalogue filters.')
    else:
        dossier_pool=all_candidates if requested_protein in set(all_candidates.sequence_id) else selected
        if st.session_state.get('dossier_protein') not in set(dossier_pool.sequence_id):
            st.session_state['dossier_protein']=sorted(dossier_pool.sequence_id)[0]
        annotations=dossier_pool.set_index('sequence_id').display_annotation.to_dict()
        protein=st.selectbox('Protein',sorted(dossier_pool.sequence_id),key='dossier_protein',format_func=lambda p:p+' · '+annotations[p])
        records=dossier_pool[dossier_pool.sequence_id.eq(protein)];row=records.iloc[0]
        st.link_button('Locate this candidate on the interactive hypothesis ↗',hypothesis_url(app_url,protein))
        st.subheader(row.display_annotation);st.caption(protein+' · '+row.species+' · catalogue family: '+row.family+' · catalogue grade '+row.grade)
        if row.reclassification_tier:
            st.write('**Local Pfam–CDD:** '+row.reclassification_family+' · '+row.reclassification_evidence_tier)
            st.write(row.reclassification_rationale)
            st.caption('Reclassification alignment: '+row.reclassification_alignment+'. Pfam–CDD evidence tier and catalogue grade are independent.')
            st.link_button('Locate the Pfam–CDD family/class on the map ↗',map_url(app_url,protein))
        tabs=st.tabs(['Overview','Domains','Motif','Topology','Orthology','Sequence & SMART'])
        with tabs[0]:table(records.T.reset_index().rename(columns={'index':'Field',records.index[0]:'Value'}))
        with tabs[1]:
            if row.reclassification_tier:
                table(records[['reclassification_family','reclassification_evidence_tier','reclassification_pfam','reclassification_cdd','reclassification_rationale','reclassification_orthogroup_context','reclassification_alignment']])
            domains=books['files/NCBI_CDD.xlsx']['NCBI_CDD_selected_hits'];domains=domains[domains.sequence_id.eq(protein)]
            st.write('Pfam: '+str(row.architecture));st.write('CDD: '+str(row.NCBI_CDD_architecture))
            if len(domains):
                domain_plot=domains.assign(span=domains.end-domains.start+1,evalue=pd.to_numeric(domains.evalue,errors='coerce'))
                plotly_chart(px.bar(domain_plot,x='span',base='start',y='short_name',orientation='h',hover_data={'accession':True,'start':True,'end':True,'evalue':':.3e'},title='CDD domain architecture',labels={'span':'Residue position','short_name':'Domain','evalue':'E-value'}),width='stretch')
            table(domains)
            domain_export=domains.copy()
            domain_export['evalue']=domain_export.evalue.map(lambda value:'' if pd.isna(value) or value=='' else format(Decimal(str(value)),'e'))
            download(domain_export,'domains_'+protein+'.csv')
        with tabs[2]:motif_view(motifs[motifs.sequence_id.eq(protein)],'dossier_motifs')
        with tabs[3]:
            topology=books['files/Topology_predictions.xlsx']['Topology_predictions'];table(topology[topology.protein_id.eq(protein)])
        with tabs[4]:
            direct=books['files/Direct_orthologues.xlsx']['Direct_orthologues'];table(direct[direct.candidate_id.eq(protein)])
            st.write('Orthogroup: '+row.orthogroup+' · '+row.orthology_scope)
        with tabs[5]:
            sequence=sequences.get(protein,'')
            if sequence:st.code('>'+protein+'\n'+sequence);st.download_button('Download original sequence',fasta_export([protein],sequences),protein+'.faa')
            else:st.info('No original sequence is present in the current family FASTAs for this protein.')
            smart_panel(protein,records,sequence)
elif page=='Comments & feedback':feedback_panel()
elif page=='Source Library':
    st.header('Source Library')
    files=source_files();inventory=pd.DataFrame([{'file':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'format':p.suffix} for p in files])
    table(inventory);download(inventory,'source_library_inventory.csv')
    path=st.selectbox('Open a source file',files,format_func=lambda p:p.relative_to(ROOT).as_posix())
    st.download_button('Download original file',path.read_bytes(),path.name)
    if path.suffix=='.xlsx':
        @st.cache_data(show_spinner=False)
        def workbook(path,mtime):return pd.read_excel(path,sheet_name=None)
        sheets=workbook(path,path.stat().st_mtime_ns);sheet=st.selectbox('Worksheet',list(sheets));table(sheets[sheet])
    elif path.suffix in ['.tsv','.csv']:
        frame=pd.read_csv(path,sep='\t' if path.suffix=='.tsv' else ',',nrows=500);table(frame);st.caption('Preview: first 500 rows. Download retains the complete original file.')
    else:st.code(path.read_text(encoding='utf-8',errors='replace')[:30000]);st.caption('Preview limited to 30,000 characters.')
    if conflicts:st.warning(f'{len(conflicts)} sequence conflicts in family FASTAs.');table(pd.DataFrame(conflicts))
elif page=='Citations':st.markdown((ROOT/'CITATIONS.md').read_text(encoding='utf-8'))

creator_credit()
