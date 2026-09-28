"""Verify the revised family counts, map bindings and downloadable hypothesis."""
import json

from streamlit.testing.v1 import AppTest

from data import ROOT, load, source_files
from prototype import FAMILY_NODES, MAP_EDGES, candidate_rows, hypothesis, interactive_html


cohorts, *_ = load()
rows = candidate_rows(cohorts['Adhesome candidates'], cohorts['FN3 / fibronectin-like review'])
assert rows.evidence_tier.value_counts().to_dict() == {
    'Core family-retained': 189, 'Provisional': 43, 'Exploratory FN3 screen': 3,
}
assert rows.map_node.notna().all()
assert all(a in FAMILY_NODES.values() and b in FAMILY_NODES.values() for a,b,_,_ in MAP_EDGES)
assert (ROOT/'Integrin_adhesome_presentation.png').is_file()
assert {p.name for p in source_files()} >= {
    'Integrin_adhesome_presentation.emf',
    'Integrin_adhesome_presentation.png',
    'Schistosome_adhesome_interactive.html',
}
html = interactive_html(ROOT/'Schistosome_adhesome_interactive.html', rows,
                        'integrin_alpha', 'Sman__Smp_126140')
assert 'Sman__Smp_126140' in html and 'atlasPayload' in html
model = hypothesis(rows, list(FAMILY_NODES), ['Core family-retained','Provisional'],
                   ['inferred','structural','exploratory'])
assert model['candidate_count'] == 232
assert model['relationship_count'] == 15  # The FN3 edge is excluded with its exploratory tier.
json.dumps(model, allow_nan=False)

app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=120).run()
assert not app.exception, [error.message for error in app.exception]
assert any('Schistosome proteomes contain a broadly shared repertoire' in item.value for item in app.markdown)
app.sidebar.radio[0].set_value('Source Library').run()
for name in ['Integrin_adhesome_presentation.emf', 'Integrin_adhesome_presentation.png',
             'Schistosome_adhesome_interactive.html']:
    next(widget for widget in app.selectbox if widget.label == 'Open a source').set_value(name).run()
    assert not app.exception, [error.message for error in app.exception]
print('PASS prototype image, audited counts, map bindings and hypothesis export')
