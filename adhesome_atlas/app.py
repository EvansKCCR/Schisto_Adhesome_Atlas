"""Multi-species Schisto-Adhesome Atlas entry point."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from atlas_styles import apply_style
from data import ROOT,load,fingerprint,source_files,fasta_export
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
apply_style()

@st.cache_data(show_spinner='Reading current annotation library…')
def cached_data(signature):return load()
cohorts,books,motifs,sequences,memberships,raw,topologies,conflicts=cached_data(fingerprint())
all_candidates=cohorts['Adhesome candidates']

def table(frame):
    shown=frame.copy()
    for c in shown:
        if shown[c].dtype==object: shown[c]=shown[c].fillna('').astype(str)
    st.dataframe(shown,hide_index=True,width='stretch')

def download(frame,name,label='Download table CSV'):
    st.download_button(label,frame.to_csv(index=False),name,'text/csv')

def motif_view(sites,key='motifs'):
    st.subheader('Motif context evidence')
    annotation=all_candidates[['sequence_id','family','species','candidate_annotation']]
    sites=sites.merge(annotation,on='sequence_id',how='left',validate='many_to_one')
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
    st.markdown('## 🧬 Schisto-Adhesome Atlas')
    st.caption('COMPARATIVE · INTEGRIN · ADHESOME')
    page=st.radio('Explore',['Introduction','Components','Interactions','Orthology','Phylogeny','Protein dossier','Motif explorer','Comments & feedback','Source Library','Citations'])
    species=st.multiselect('Species',sorted(all_candidates.species.unique()),default=sorted(all_candidates.species.unique()))
    families=st.multiselect('Protein families',sorted(all_candidates.family.unique()))
    classification=st.selectbox('Classification',['All','Supported','Provisional'])
    query=st.text_input('Search annotations')
    figure_download_settings()
    if st.button('Reload source files'):st.cache_data.clear();st.rerun()
    st.caption(f'{len(all_candidates):,} candidates · {all_candidates.species.nunique()} species · {all_candidates.family.nunique()} families')
selected=all_candidates[all_candidates.species.isin(species)].copy()
if families:selected=selected[selected.family.isin(families)]
if classification!='All':selected=selected[selected.audit_classification.eq(classification)]
if query:selected=selected[selected.fillna('').astype(str).apply(lambda s:s.str.contains(query,case=False,regex=False)).any(axis=1)]

if page=='Introduction':
    identity_banner()
    st.markdown('<div class="hero"><div class="eyebrow">COMPARATIVE ADHESION BIOLOGY</div><h1>Schisto-Adhesome Atlas</h1><p>Explore the protein families, evolutionary relationships and interaction hypotheses of the schistosome integrin adhesome.</p></div>',unsafe_allow_html=True)
    st.subheader('About the Schisto-Adhesome Atlas')
    st.write('The Schisto-Adhesome Atlas is an interactive platform for exploring adhesion-associated proteins across medically important Schistosoma species. It integrates protein annotations, orthology, phylogeny, conserved domains and motif exploration to reveal evolutionary relationships, parasite-specific features and potential functional interaction modules. By connecting comparative bioinformatics with experimental prioritization, the Atlas supports the discovery of candidate drug targets, vaccine antigens and biomarkers for schistosomiasis research.')
    for col,label,value in zip(st.columns(4),['Candidates','Species','Families','Orthogroups'],[len(all_candidates),all_candidates.species.nunique(),all_candidates.family.nunique(),all_candidates.loc[all_candidates.orthogroup.ne(''),'orthogroup'].nunique()]):col.metric(label,value)
    st.subheader('Explore the interactive adhesome hypothesis')
    network_dir=ROOT/'adhesome_network'
    path=next((network_dir/name for name in ['Schistosome_adhesome_interactive.html','Schistosome_adhesome_rebuilt.html'] if (network_dir/name).exists()),None)
    if path:
        html=path.read_text(encoding='utf-8').replace('previously supplied model','adhesome model in the library')
        html=html.replace('</head>','<style>svg text{fill:#000!important;font-family:Arial,sans-serif}</style></head>')
        sim=ROOT/SIMULATOR_FILE
        if sim.exists():html=linked_explorer_html(html,simulator_html(sim,all_candidates))
        st.iframe(html,height=1050)
        st.download_button('Download interactive map and linked simulator',html,'Schisto_Adhesome_interactive.html','text/html')
        st.caption('Select a family on the map to inspect its evidence and open its linked downstream simulation. Simulator weights are conceptual parameters; metazoan reference evidence counts are not used as binding affinities.')
    else:st.info('No interactive map is present in the current network library.')
    st.subheader('Build an evidence-stratified schistosome adhesome hypothesis')
    st.write('Use Interactions to choose species, grades and families, construct the orthogroup consensus graph, and download membership, reference-edge evidence, centrality and provenance.')

elif page=='Components':
    view=st.radio('Component view',['Summary statistics','Summary graphs','Candidate catalogue','Family assignment audit','Comparative lab','Candidate prioritization'],horizontal=True)
    if view in ['Summary statistics','Summary graphs','Comparative lab']:
        counts=selected.groupby(['species','family']).sequence_id.nunique().reset_index(name='Proteins')
        if view=='Summary statistics':table(selected.groupby(['species','grade','assignment_confidence']).size().reset_index(name='Candidates'))
        elif view=='Summary graphs':
            if len(counts):plotly_chart(px.bar(counts,x='family',y='Proteins',color='species'),width='stretch')
            if len(selected):plotly_chart(px.treemap(selected.groupby(['module','family']).size().reset_index(name='Proteins'),path=['module','family'],values='Proteins',color='module'),width='stretch')
        else:
            matrix=counts.pivot(index='family',columns='species',values='Proteins').fillna(0)
            if len(matrix):plotly_chart(px.imshow(matrix,aspect='auto',height=max(500,len(matrix)*23),title='Family repertoire across species'),width='stretch')
            download(matrix.reset_index(),'family_species_counts.csv')
    elif view=='Candidate prioritization':
        st.write('Rank candidates using the current audited evidence scores. Orthology benchmark weights and family confidence are retained. Scores are separate from reference-network centrality; domain architecture, topology and motif context remain explicit supporting evidence.')
        metric=st.selectbox('Rank by',['total_score_0_10','domain_score_0_4','orthology_score_0_3','motif_score_0_2','localization_score_0_1'])
        ranked=selected.sort_values(metric,ascending=False).reset_index(drop=True);ranked.insert(0,'rank',range(1,len(ranked)+1))
        table(ranked);download(ranked,'candidate_prioritization.csv')
    elif view=='Family assignment audit':
        table(selected[['sequence_id','species','family','protein_name','grade','assignment_confidence','family_support_level','annotation_resolution','family_decision','identity_rule','identity_competitors','alternative_family_hypotheses','equally_ranked_hypotheses']]);download(selected,'family_assignment_audit.csv')
    else:table(selected);download(selected,'candidate_catalogue.csv')

elif page=='Interactions':
    workspace=st.radio('Network workspace',['Curated orthogroup consensus','STRING query & import'],horizontal=True)
    if workspace=='Curated orthogroup consensus':consensus_panel(all_candidates)
    else:string_panel(all_candidates)

elif page=='Orthology':orthology_panel(all_candidates)
elif page=='Phylogeny':
    @st.fragment(run_every='30s')
    def live_phylogeny():phylogeny_panel(all_candidates)
    live_phylogeny()

elif page=='Motif explorer':motif_view(motifs[motifs.sequence_id.isin(selected.sequence_id)])
elif page=='Protein dossier':
    st.header('Protein dossier')
    if selected.empty:st.info('No proteins match the catalogue filters.')
    else:
        protein=st.selectbox('Protein',sorted(selected.sequence_id),format_func=lambda p:p+' · '+selected.set_index('sequence_id').loc[p,'candidate_annotation'])
        records=selected[selected.sequence_id.eq(protein)];row=records.iloc[0]
        st.subheader(row.candidate_annotation);st.caption(protein+' · '+row.species+' · '+row.family+' · '+row.grade)
        tabs=st.tabs(['Overview','Domains','Motif','Topology','Orthology','Sequence & SMART'])
        with tabs[0]:table(records.T.reset_index().rename(columns={'index':'Field',records.index[0]:'Value'}))
        with tabs[1]:
            domains=books['files/NCBI_CDD.xlsx']['NCBI_CDD_selected_hits'];domains=domains[domains.sequence_id.eq(protein)]
            st.write('Pfam: '+str(row.architecture));st.write('CDD: '+str(row.NCBI_CDD_architecture))
            if len(domains):
                domain_plot=domains.assign(span=domains.end-domains.start+1)
                plotly_chart(px.bar(domain_plot,x='span',base='start',y='short_name',orientation='h',hover_data=['accession','start','end','evalue'],title='CDD domain architecture',labels={'span':'Residue position','short_name':'Domain'}),width='stretch')
            table(domains);download(domains,'domains_'+protein+'.csv')
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
