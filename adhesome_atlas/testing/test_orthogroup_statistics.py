"""Source reconciliation, filtering, linked exploration and optional Streamlit UI regression."""
from bootstrap import ATLAS_ROOT
import hashlib
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs,urlsplit

import pandas as pd

from data import ROOT,adapt_candidate_library
from orthogroup_statistics import (FILES,SPECIES,SUMMARY,CLASSIFICATIONS,load_statistics,summary,
    signature,filter_groups,species_table,species_detail,related_candidates,chart,catalogue_statistics,
    catalogue_exact_profiles,GRADE_COLUMNS,supported_family_labels)


def candidates_from_workbook():
    raw=pd.read_excel(ROOT/'files/adhesome_candidates_list.xlsx',sheet_name='Audited_family_assignment')
    return adapt_candidate_library(raw)


def fixtures(master,sources):
    with tempfile.TemporaryDirectory(prefix='orthogroup_stats_test_',dir=ROOT) as temporary:
        folder=Path(temporary)
        def restore():
            for key,name in FILES.items():sources[key].to_csv(folder/name,sep='\t',index=False)
        restore();initial=signature(folder)
        # New observed copy profiles are retained without hardcoded 1:1/2:2 assumptions.
        added=sources['all'].iloc[[0]].copy();added['Orthogroup']='OG_TEST';added['Copy profile']='3:3'
        added[[s+' copies' for s in SPECIES]]=3;added['Total candidates']=21
        pd.concat([sources['all'],added]).to_csv(folder/FILES['all'],sep='\t',index=False)
        new,_,_=load_statistics(folder)
        assert len(new)==len(master)+1 and len(filter_groups(new,profiles=['3:3']))==1
        assert signature(folder)!=initial
        restore()
        focused=sources['1:1'].copy();focused.loc[0,'Supported copies']+=1
        focused.to_csv(folder/FILES['1:1'],sep='\t',index=False)
        kept,_,checks=load_statistics(folder)
        pd.testing.assert_frame_equal(kept,master)
        assert checks.Issue.str.contains('complete values retained').any()
        restore()
        outside=sources['1:1'].iloc[[0]].assign(Orthogroup='OG_OUTSIDE')
        pd.concat([sources['1:1'],outside]).to_csv(folder/FILES['1:1'],sep='\t',index=False)
        kept,_,checks=load_statistics(folder)
        assert len(kept)==len(master) and checks.Issue.str.contains('Absent from complete').any()
        restore()
        pd.concat([sources['all'],sources['all'].iloc[[0]]]).to_csv(folder/FILES['all'],sep='\t',index=False)
        kept,_,checks=load_statistics(folder)
        assert len(kept)==len(master) and checks.Issue.str.contains('identical duplicate').any()
        conflict=sources['all'].iloc[[0]].copy();conflict['Total candidates']+=1
        pd.concat([sources['all'],conflict]).to_csv(folder/FILES['all'],sep='\t',index=False)
        try:load_statistics(folder)
        except ValueError as error:assert 'conflicting rows' in str(error)
        else:raise AssertionError('Conflicting duplicate summaries must not be silently selected')
        restore()
        bad=sources['all'].copy();bad.loc[0,'Total candidates']=-1
        bad.to_csv(folder/FILES['all'],sep='\t',index=False)
        try:load_statistics(folder)
        except ValueError as error:assert 'non-negative integer' in str(error)
        else:raise AssertionError('Negative counts accepted')
        restore();bad=sources['all'].drop(columns=SPECIES[-1]+' supported')
        bad.to_csv(folder/FILES['all'],sep='\t',index=False)
        try:load_statistics(folder)
        except ValueError as error:assert SPECIES[-1] in str(error)
        else:raise AssertionError('Missing species silently accepted')
    print('PASS changed/new profiles, signature refresh, authoritative-master conflicts, focused subsets, '
          'duplicate/invalid rows and seven-species schema checks',flush=True)


def ui_tests(master):
    from streamlit.testing.v1 import AppTest
    from orthogroup_dashboard import PREFIX
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=180)
    app.session_state['atlas_page']='Orthology';app.run()
    assert not app.exception,[e.message for e in app.exception]
    def select(label,value):
        next(widget for widget in app.selectbox if widget.label==label).set_value(value).run()
        assert not app.exception,[(label,e.message) for e in app.exception]
    if any(widget.label=='Orthogroup report' for widget in app.selectbox):select('Orthogroup report','Exact copy profiles')
    for label in ['302','156','21','1,416 / 2,373','169','11','122','585 / 0 / 831 / 0']:
        assert label in [metric.value for metric in app.metric],label
    for visual in ['Family composition','Species heatmap','Classification','Specific and broad support','Species representation','Copy profiles']:
        select('Orthogroup visualization',visual)
    select('Copy-profile dataset','Supported 1:1 subset')
    assert app.metric[0].value==str(len(master[master['In supported 1:1 subset']]))
    select('Copy-profile dataset','Supported 2:2 subset')
    assert app.metric[0].value==str(len(master[master['In supported 2:2 subset']]))
    select('Copy-profile dataset','All exact profiles')
    next(w for w in app.text_input if w.label=='Find an orthogroup, copy profile or reported family').set_value('OG0000076').run()
    assert not app.exception,[e.message for e in app.exception]
    assert app.metric[0].value=='1'
    assert any('OG0000076' in heading.value for heading in app.subheader)
    next(w for w in app.text_input if w.label=='Find an orthogroup, copy profile or reported family').set_value('NO_SUCH_GROUP').run()
    assert not app.exception and app.metric[0].value=='0'
    next(w for w in app.button if w.label=='Reset orthogroup filters').click().run()
    assert not app.exception and app.metric[0].value=='302'
    select('Orthology workspace','Candidate & reference orthologues')
    assert any(w.label=='Orthology collection' for w in app.selectbox)
    assert not app.exception
    print('PASS Streamlit Orthology startup, six visualizations, both subset selectors, exact search, detail, '
          'empty state, reset and preserved reference-orthologue workspace',flush=True)


def catalogue_checks(candidates):
    catalogue=catalogue_statistics(candidates)
    exact,sources=catalogue_exact_profiles(catalogue)
    counts=summary(exact)
    assert len(catalogue)==579
    assert [counts[key] for key in ('Orthogroups','Supported 1:1','Supported 2:2','Supported copies','Total candidates')]==[302,156,21,1416,2373]
    assert [counts[column] for column in GRADE_COLUMNS]==[585,0,831,0]
    assert [counts[label] for label in CLASSIFICATIONS]==[169,11,122]
    assert exact['Copy profile'].value_counts().to_dict()=={'1:1':269,'2:2':29,'3:3':4}
    assert counts['Represented species']==7
    assert exact[GRADE_COLUMNS].sum(axis=1).eq(exact['Supported copies']).all()
    assert set(filter_groups(exact,support='Grade C support').Orthogroup)==set(exact[exact['Supported grade C'].gt(0)].Orthogroup)
    assert all(set(sources[profile].Orthogroup)<=set(sources['all'].Orthogroup) for profile in ('1:1','2:2'))
    mixed=filter_groups(exact,query='OG0001975',families=['FAK'])
    assert len(mixed)==1 and mixed.iloc[0]['Supported family counts']=='FAK (6); Protein kinase superfamily (subtype unresolved) (1)'
    assert 'FAK' in supported_family_labels(mixed)
    composition,_=chart(mixed,'Family composition')
    assert set(composition.data[0].y)=={'FAK','Protein kinase superfamily (subtype unresolved)'}

    group=candidates[candidates.orthogroup.eq('OG0001975')].copy()
    repeated=pd.concat([group,group.iloc[[0]]],ignore_index=True)
    pd.testing.assert_frame_equal(catalogue_statistics(repeated),catalogue_statistics(group))
    updated=group.copy()
    updated.loc[updated.family_support_level.eq('broad supported'),'family_support_level']='unresolved'
    row=catalogue_statistics(updated).iloc[0]
    assert row['Supported copies']==6 and row['Supported grade C']==0 and row['Total candidates']==7
    assert row.Classification==CLASSIFICATIONS[1]
    extra=group.iloc[[0]].assign(sequence_id='Test__second_copy')
    new=catalogue_statistics(pd.concat([group,extra],ignore_index=True))
    assert new.iloc[0]['Total candidates']==8 and catalogue_exact_profiles(new)[0].empty
    print('PASS current seven-species profiles, audited grade C support, mixed-family filters and catalogue mutation',flush=True)
    return exact


def main():
    folder=ROOT/'orthology';paths=[folder/name for name in FILES.values()]
    hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    master,sources,checks=load_statistics(folder);assert checks.empty,checks.to_dict('records')
    raw=pd.read_csv(paths[0],sep='\t',keep_default_na=False)
    pd.testing.assert_frame_equal(master[raw.columns],raw)
    counts=summary(master)
    assert counts['Orthogroups']==raw.Orthogroup.nunique()==298
    assert counts['Supported 1:1']==sources['1:1'].Orthogroup.nunique()==51
    assert counts['Supported 2:2']==sources['2:2'].Orthogroup.nunique()==12
    assert counts['Supported copies']==488 and counts['Total candidates']==2289
    assert [counts[c] for c in CLASSIFICATIONS]==[49,14,235]
    assert counts['Supported grade A']==488 and counts['Supported grade B']==0
    assert counts['Specific supported']==433 and counts['Broad supported']==55
    assert len(species_table(master))==counts['Represented species']==7
    assert species_table(master)['Total copies'].sum()==counts['Total candidates']
    assert species_table(master)['Supported copies'].sum()==counts['Supported copies']
    for profile in ['1:1','2:2']:
        assert set(filter_groups(master,subset='Supported '+profile+' subset').Orthogroup)==set(sources[profile].Orthogroup)
    for sp in SPECIES:
        filtered=filter_groups(master,species=[sp],species_basis='Supported copies')
        assert set(filtered.Orthogroup)==set(raw.loc[raw[sp+' supported'].gt(0),'Orthogroup'])
    family=raw.loc[raw['Supported family identity'].ne(''),'Supported family identity'].iloc[0]
    assert filter_groups(master,families=[family])['Supported family identity'].eq(family).all()
    assert filter_groups(master,classifications=[CLASSIFICATIONS[0]]).Classification.eq(CLASSIFICATIONS[0]).all()
    assert filter_groups(master,support='Broad family support')['Broad supported'].gt(0).all()
    assert filter_groups(master,support='Grade B support').empty
    assert filter_groups(master,query='NO_SUCH_GROUP').empty
    candidates=candidates_from_workbook();live=catalogue_checks(candidates)
    linked=related_candidates(candidates,'OG0000076','https://atlas.example/')
    assert len(linked)==len(candidates[candidates.orthogroup.eq('OG0000076')]) and not linked.empty
    for _,row in linked.iterrows():
        assert parse_qs(urlsplit(row['Protein dossier']).query)=={'view':['Protein dossier'],'protein':[row.sequence_id]}
    detail=species_detail(master.iloc[0]);assert detail['Total copies'].sum()==master.iloc[0]['Total candidates']
    from orthogroup_dashboard import selection_patch,chart_selection,PREFIX,st
    from unittest.mock import patch
    old_key=PREFIX+'chart_Copy profiles_0';new_key=PREFIX+'chart_Classification_1'
    state={PREFIX+'visual':'Classification',PREFIX+'selection_revision':1,
        old_key:{'selection':{'points':[{'customdata':['1:1']}]}},
        new_key:{'selection':{'points':[{'customdata':[CLASSIFICATIONS[0]]}]}}}
    with patch.object(st,'session_state',state):
        chart_selection(old_key,'profiles');assert PREFIX+'profiles' not in state
        chart_selection(new_key,'classifications');assert state[PREFIX+'classifications']==[CLASSIFICATIONS[0]]
    for visual in ['Copy profiles','Family composition','Species heatmap','Classification','Specific and broad support','Species representation']:
        fig,event=chart(master,visual)
        assert fig.data and event
        assert all(len(trace.customdata)>0 for trace in fig.data if trace.customdata is not None)
        if visual=='Species heatmap':
            assert fig.data[0].zmin==0 and fig.data[0].colorbar.tickformat=='d'
            assert fig.data[0].texttemplate=='%{z}' and fig.data[0].xgap==2
            point=fig.data[-1].customdata[0]
            assert selection_patch(event,{'customdata':point})=={PREFIX+'focus':point[0]}
            assert point[2]==int(raw.set_index('Orthogroup').loc[point[0],point[1]+' copies'])
        elif visual=='Family composition':
            assert selection_patch(event,{'customdata':[family]})=={PREFIX+'families':[family]}
    from research_priorities import apply_target_route
    state={};apply_target_route(candidates,{'view':'Phylogeny','orthogroup':'OG0000076'},state)
    assert state['atlas_page']=='Phylogeny' and state['phylogeny_route_group']=='OG0000076'
    state={};apply_target_route(candidates,{'view':'Orthology','orthogroup':'OG0000076'},state)
    state['orthology_route_group']='';apply_target_route(candidates,
        {'view':'Orthology','orthogroup':'OG0000076','workspace':'references'},state)
    assert state['orthology_route_group']=='OG0000076'
    fixtures(master,sources)
    assert hashes=={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    print('PASS 298 unique groups, 51/12 supported subsets, 488/2289 supported/total copies, 49/14/235 classes, '
          'seven species, A/B and specific/broad sums; six chart models, exact links, click metadata and unchanged TSVs',flush=True)
    if '--app' in sys.argv:ui_tests(live)


if __name__=='__main__':main()
