"""Real-data checks and independent small-graph centrality checks."""
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from streamlit.testing.v1 import AppTest
from data import load
from networks import load_network
from reconstruction import assemble,topology,prioritize,read_optional

candidates=load()[0]['Adhesome candidates']
nodes,edges,excluded=assemble(candidates,load_network,.4)
assert len(nodes)==150 and len(edges)==907
assert not len(excluded)
metrics,graph=topology(nodes,edges)
assert graph.number_of_nodes()==150 and graph.number_of_edges()==907
assert sum(dict(graph.degree()).values())==1814
ranking=prioritize(metrics,graph,nodes)
assert ranking.integrated_score.isna().all()
assert ranking.conservation.notna().any()
assert nodes.orthogroup.ne('').any()
assert ranking.host_similarity_flag.eq('Not assessed').all()

# A three-node path plus an isolate: center is a bottleneck; isolate stays zero.
small=pd.DataFrame({'identifier':['a','b','c','d'],'layer':['Membrane','Membrane-proximal','Actin-coupling','Unresolved']})
links=pd.DataFrame({'node1_string_id':['a','b'],'node2_string_id':['b','c']})
m,g=topology(small,links)
assert m.set_index('identifier').loc['b','degree']==2
assert abs(m.set_index('identifier').loc['b','betweenness']-1/3)<1e-8
assert m.set_index('identifier').loc['d','closeness']==0
assert m.set_index('identifier').loc['b','interface_connections']==2

# Incomplete transfer is excluded; cited, fully supported within-species transfer is accepted.
pair=nodes[nodes.species.eq('Shae')].identifier.head(2).tolist()
cols=['source','target','relation','orthology_transfer','domain_compatibility','motif_compatibility','topology_compatibility','family_relationship','phylogenetic_support','reference']
record=dict.fromkeys(cols,'supported');record.update(source=pair[0],target=pair[1],relation='Domain-mediated association',reference='TEST ONLY â€” not saved')
def fixture(name,columns):
    return pd.DataFrame([record]) if name=='reference_interactions.tsv' else read_optional(name,columns)
with patch('reconstruction.read_optional',side_effect=fixture):
    n,e,x=assemble(candidates,load_network,.4)
    assert len(e)==908 and x.empty
record['motif_compatibility']='unassessed'
with patch('reconstruction.read_optional',side_effect=fixture):
    n,e,x=assemble(candidates,load_network,.4)
    assert len(e)==907 and len(x)==1

app=AppTest.from_file(str(Path(__file__).with_name('app.py')),default_timeout=90).run()
assert not app.exception,[e.message for e in app.exception]
app.sidebar.radio[0].set_value('Interactions').run()
assert not app.exception,[e.message for e in app.exception]
for view in ['Shae','Sjap','Sman','Orthogroup consensus','Pan-schistosome · separate proteins']:
    app.selectbox(key='reconstruction_view').set_value(view).run()
    assert not app.exception,[e.message for e in app.exception]
    print('PASS',view,flush=True)
app.slider(key='reconstruction_threshold').set_value(1.).run()
assert not app.exception,[e.message for e in app.exception]
print('PASS real-data topology, missing-evidence scoring, transfer gates, empty graph and views',flush=True)
