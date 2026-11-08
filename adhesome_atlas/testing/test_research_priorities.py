"""Validate brief fidelity, exact candidate links, discrepancy reporting and deep-link state."""
from bootstrap import ATLAS_ROOT
import hashlib
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
import pandas as pd
import tempfile
import re
import sys
from research_priorities import (load_brief,comparisons,protein_matches,protein_links,
    target_url,apply_target_route,feature_card,rich_text,available_families,TABLE_HEADERS,_table_block)


def format_checks(text,brief,folder):
    for delimiter in ['tabs','pipes']:
        lines=text.splitlines();blocks=[]
        for first_header,headers in TABLE_HEADERS.items():
            rows,start,end=_table_block(text,first_header)
            if delimiter=='tabs':replacement=['\t'.join(headers)]+['\t'.join(row.values()) for row in rows]
            else:replacement=['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(row.values())+' |' for row in rows]
            blocks.append((start,end,replacement))
        for start,end,replacement in sorted(blocks,reverse=True):lines[start:end]=replacement
        path=folder/(delimiter+'.md');path.write_text('\n'.join(lines),encoding='utf-8')
        parsed=load_brief(path)
        assert parsed==brief,(delimiter,'All scientific fields must survive explicit table delimiters')
    legacy=re.sub(r'\[([^\]]+)\]\((https://doi\.org/[^)]+)\)',lambda match:'('+match[1]+')['+match[2]+']',text)
    path=folder/'legacy-citations.md';path.write_text(legacy,encoding='utf-8')
    parsed=load_brief(path)
    assert parsed['references']==brief['references']
    # Ambiguous plain prose must request explicit boundaries, not shift cells.
    row=next(line for line in text.splitlines() if line.startswith('Selectivity'))
    malformed=text.replace(row,row.replace('\t',' ').replace('Low risk of antibody cross-reactivity with host proteins','Low risk in Humans and low antibody cross-reactivity with host proteins'))
    path=folder/'ambiguous.md';path.write_text(malformed,encoding='utf-8')
    try:load_brief(path)
    except ValueError as error:assert 'use tabs or Markdown pipes' in str(error)
    else:raise AssertionError('Ambiguous plain-table cells must be rejected')


def main():
    root=Path(__file__).resolve().parents[1]
    source=root/'notes/Target_prioritization.md';workbook=root/'files/adhesome_candidates_list.xlsx'
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,workbook)}
    brief=load_brief(source)
    from data import adapt_candidate_library
    candidates=adapt_candidate_library(pd.read_excel(workbook,sheet_name='Audited_family_assignment'))
    assert [[m['count'] for m in f['metrics']] for f in brief['features']]==[[159,13],[41,4],[17,7]]
    assert [r['count'] for r in brief['additional']]==[30,6,8,14,14,14,117,14,14,7,7,9,25,20,35,14,14,7,37,16,14]
    assert len(brief['framework'])==6 and len(brief['roadmap'])==14 and len(brief['references'])==29
    assert brief['roadmap'][-1]=={
        'Candidate or orthogroup':'OG0000056 ADAM-like + OG0000629 KCNH-like',
        'Development objective':'Membrane-protein target discovery',
        'First decisive experiment or analysis':'Surface metalloprotease activity and channel electrophysiology as separate target tracks',
    }
    assert 'Library-based prioritization context.' in brief['priority_context']
    assert any('pmc.ncbi.nlm.nih.gov' in ref['url'] for ref in brief['references'])
    assert 'receptor-proximal scaffold priorities' in brief['additional_evidence']
    assert 'For practical ranking' in brief['framework_text']
    assert brief['repeated_roadmap_rows']==1
    assert sum('Sm-p80' in row['Candidate or orthogroup'] for row in brief['roadmap'])==1
    assert 'three categories' in brief['overview']
    assert 'tetraspanin-family candidates' in ' '.join(brief['features'][0]['evidence'])
    assert 'Candidate family' not in ' '.join(brief['features'][2]['evidence'])
    assert 'Src-family kinases' not in ' '.join(brief['features'][2]['evidence'])
    assert 'Protein ID Assignment Main justification' not in ' '.join(brief['features'][2]['evidence'])
    with tempfile.TemporaryDirectory(prefix='priority_parser_test_',dir=root) as temporary:
        folder=Path(temporary).resolve();assert folder.is_relative_to(root.resolve())
        format_checks(source.read_text(encoding='utf-8-sig'),brief,folder)
        alternate=folder/'brief.md'
        for term,classification in [('unresolved','Unassigned'),('unassigned','Unassigned'),('provisional','Provisional')]:
            line=brief['features'][2]['count_text']
            alternate.write_text(source.read_text(encoding='utf-8').replace(line,line+'; nine '+term+' integrin α hypotheses'),encoding='utf-8')
            assert load_brief(alternate)['features'][2]['metrics'][2]['classification']==classification
    checks=comparisons(brief,candidates)
    assert len(checks)==27 and all(r['matches'] for r in checks),checks
    legacy=candidates.copy()
    legacy['family']=legacy.family.replace({'tetraspanin-like':'tetraspanin_like','calpain-like':'calpain_like',
        'integrin alpha':'integrin_alpha','integrin beta':'integrin_beta',
        'collagen-like':'collagen_like','laminin-like':'laminin_like'})
    assert all(row['matches'] for row in comparisons(brief,legacy))
    base='https://atlas.example/science/atlas?old=1'
    for f in brief['features']:
        html=feature_card(f,candidates,base)
        assert 'unavailable' not in html and 'target="_self"' in html
        for identifier in f['proteins']:assert len(protein_matches(candidates,identifier))==1
        for group in f['orthogroups']:assert group in set(candidates.orthogroup)
    for row in brief['additional']:
        assert 'unavailable' not in rich_text(row['Representative S. mansoni IDs'],candidates,base)
        assert all(available_families((family,),candidates) for family in row['families'])
    for row in brief['roadmap']:
        assert 'unavailable' not in rich_text(row['Candidate or orthogroup'],candidates,base)
    for reference in brief['references']:
        standard=f'[{reference["label"]}]({reference["url"]})'
        legacy=f'({reference["label"]})[{reference["url"]}]'
        assert rich_text(standard,candidates,base)==rich_text(legacy,candidates,base)
        assert f'href="{reference["url"]}"' in rich_text(standard,candidates,base)
    assert '&lt;script&gt;' in rich_text('<script>alert(1)</script>',candidates,base)
    assert 'unavailable' in protein_links('Smp_missing',candidates,base)
    registry={'protein_links':[dict(protein_id='Sman__Smp_020540',published_locus='Smp_020540.2',match_level='published_named_protein')]}
    published=rich_text('Smp_020540.2',candidates,base,registry)
    assert '>Smp_020540.2</a>' in published and 'protein=Sman__Smp_020540' in published
    assert 'catalogue locus' in published and 'unavailable' in rich_text('Smp_020540.99',candidates,base,registry)
    duplicated=pd.concat([candidates,pd.DataFrame([dict(sequence_id='Other__Smp_089700',family='integrin_beta',audit_classification='Supported')])],ignore_index=True)
    assert protein_links('Smp_089700',duplicated,base).count('class="research-link research-protein"')==2
    removed=candidates.drop(candidates[candidates.family.isin(available_families(('tetraspanin_like',),candidates))].index[0])
    diff=comparisons(brief,removed)[0]
    assert diff['brief']==159 and diff['live']==158 and not diff['matches']
    assert 'differs from brief' in feature_card(brief['features'][0],removed,base)
    for view,key,value in [('Protein dossier','protein','Sman__Smp_089700'),('Components','family','kindlin'),('Orthology','orthogroup','OG0006637')]:
        url=target_url(base,view,**{key:value});parsed=urlsplit(url)
        assert parsed.path=='/science/atlas' and parse_qs(parsed.query)=={'view':[view],key:[value]}
        state={};params={'view':view,key:value};apply_target_route(candidates,params,state)
        assert state['atlas_page']==view
        if key=='protein':assert state['dossier_protein']==value
        elif key=='family':assert state['catalogue_families']==[value] and state['component_section']=='Candidate catalogue'
        else:assert state['orthology_query']==value and state['orthology_route_group']==value
        state['atlas_page']='Interactions';apply_target_route(candidates,params,state)
        assert state['atlas_page']=='Interactions','Deep link must not override later manual navigation'
    assert before=={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in before}
    print('PASS TSV/Markdown tables and ambiguous-prose detection; DOI/PubMed links; expanded scientific narrative; all current catalogue counts, exact candidate links, mismatch alerts and unchanged sources',flush=True)


def app_checks():
    from streamlit.testing.v1 import AppTest
    source='''
from pathlib import Path
import streamlit as st
from data import ROOT
from test_orthogroup_statistics import candidates_from_workbook
from research_priorities import research_priorities_panel
@st.cache_data
def fixture():return candidates_from_workbook()
research_priorities_panel(fixture(),'http://localhost:8511/',ROOT/'notes/Target_prioritization.md')
'''
    app=AppTest.from_string(source,default_timeout=120).run()
    assert not app.exception,[error.message for error in app.exception]
    assert not app.warning,[warning.value for warning in app.warning]
    html='\n'.join(item.value for item in app.markdown)
    assert html.count('class="research-card"')==3
    assert html.count('class="research-step"')==14
    assert html.count('class="research-additional"')==21
    assert 'three categories' in html and 'Smp_170280' in html
    assert '<strong>Library-based prioritization context.</strong>' in html
    assert 'href="https://pmc.ncbi.nlm.nih.gov/articles/PMC9892292/"' in html
    assert 'research-difference' not in html
    assert any('repeated roadmap entry' in caption.value for caption in app.caption)
    assert len(re.findall(r'\[.+?\]\(https://(?:doi.org|pubmed.ncbi.nlm.nih.gov)/',html))>=19
    app.radio[0].set_value('Vaccine / antibody candidates').run()
    assert not app.exception
    matrix=next(item.value for item in app.markdown if 'research-matrix' in item.value)
    assert '<th scope="col">Vaccine/antibody candidate</th>' in matrix and 'Small-molecule drug candidate' not in matrix
    assert 'Smp_171530' in html and 'receptor-proximal scaffold priorities' in html
    print('PASS Streamlit context, expanded cards and references, 14 unique roadmap entries, framework controls and mismatch-only flags',flush=True)


if __name__=='__main__':
    main()
    if '--app' in sys.argv:app_checks()
