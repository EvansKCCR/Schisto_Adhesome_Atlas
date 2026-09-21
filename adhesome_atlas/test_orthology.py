"""Orthology is never a membership shortcut; check new workbook and export schemas."""
from pathlib import Path
import pandas as pd
from streamlit.testing.v1 import AppTest
from data import load, source_files
from evidence import annotate, PRIORITIES
from networks import load_network
from reconstruction import assemble, topology, prioritize

cohorts,books,*_=load()
fn=cohorts['FN3 / fibronectin-like review']
assert len(fn)==89 and 'Orthogroup' in fn
assert [fn.loc[fn.priority_group.eq(g),'sequence_id'].nunique() for g in PRIORITIES]==[8,4,10]
assert all('Not established by orthology' in v for v in fn.adhesome_interpretation)
assert fn.loc[fn.priority_group.eq(PRIORITIES[2]),'topology_evidence'].str.contains('discordance').any()
assert len(fn[fn.priority_group.eq('Other / unresolved FN3 candidates')])==67

# A mapped conserved generic kinase is not promoted; architecture is unresolved.
row={'family':'generic_kinase_screen','assigned_family':None,'module':'downstream_signalling','Orthology_Orthogroup':'TEST','Orthology_mapping_status':'matched','Orthology_HOG_status':'shared HOG'}
result=annotate(pd.DataFrame([row])).iloc[0]
assert result.evidence_review_stage.startswith('2')
assert result.adhesome_interpretation.startswith('Not established')
# Even coherent proxies stop at biological review; no positive membership label.
row.update(domain_match=True,DeepTMHMM='GLOB',**{'DeepLoc_2.1':'Cytoplasm','MotifScan_context_state':'region_supported'})
result=annotate(pd.DataFrame([row])).iloc[0]
assert result.evidence_review_stage.startswith('5')
assert result.adhesome_interpretation.startswith('Not established')

candidates=pd.concat([cohorts['Adhesome candidates'],fn],ignore_index=True)
nodes,edges,_=assemble(candidates,load_network,.4)
assert len(nodes)==150 and len(edges)==907
assert nodes.loc[nodes.species.eq('Shae'),'sequence_id'].eq('').all()
assert nodes.loc[nodes.species.eq('Sjap'),'sequence_id'].ne('').sum()==52
assert nodes.loc[nodes.species.eq('Sman'),'sequence_id'].ne('').sum()==28
assert nodes.orthogroup.ne('').any()
metrics,graph=topology(nodes,edges)
rank=prioritize(metrics,graph,nodes)
assert rank.integrated_score.isna().all()
assert rank.conservation.notna().any()
assert {'.xml','.all'} <= {p.suffix for p in source_files()}

app=AppTest.from_file(str(Path(__file__).with_name('app.py')),default_timeout=120).run()
assert not app.exception and not app.error,[e.message for e in app.exception]
app.sidebar.radio[0].set_value('Components').run()
for view in ['Orthology & evidence','FN3 / RPTP priorities']:
    app.sidebar.radio[1].set_value(view).run()
    assert not app.exception,[e.message for e in app.exception]
    print('PASS',view,flush=True)
app.sidebar.radio[0].set_value('Interactions').run()
app.selectbox(key='reconstruction_view').set_value('Orthogroup consensus').run()
assert not app.exception,[e.message for e in app.exception]
next(r for r in app.radio if r.label=='Network workspace').set_value('Species STRING explorer').run()
for code in ['Shae','Sjap','Sman']:
    app.selectbox(key='interactions_species').set_value(code).run()
    assert not app.exception,[e.message for e in app.exception]
    print('PASS resources',code,flush=True)
print('PASS orthology mapping, hierarchy, priority separation, consensus and resource views',flush=True)
