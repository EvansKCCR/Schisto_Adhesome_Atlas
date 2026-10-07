"""Supply audited inventories and mapped STRING weights to the matrix simulator."""

import json
from pathlib import Path
import streamlit as st
from nanoscale_architecture import architecture_json
import re


SIMULATOR_FILE = 'schistosome_integrin_adhesome_hypothesis_simulator.html'
INVENTORY_MARKER = 'const atlasInventory = {};'
TOPOLOGY_MARKER = 'const atlasTopology = {};'
FAMILIES = ('integrin_alpha', 'integrin_beta', 'talin', 'vinculin', 'FAK', 'Src')
PAIRS = [('IT','integrin_beta','talin',.85),('TV','talin','vinculin',.30),
         ('IV','integrin_beta','vinculin',.05)]
SPECIES = {
    'sh': 'S. haematobium',
    'sj': 'S. japonicum',
    'sm': 'S. mansoni',
}


def supported_inventory(adhesome):
    """Count distinct supported proteins, without transferring reference counts."""
    retained = adhesome[adhesome.audit_classification.eq('Supported')]
    inventory = {}
    for code, species in [('pan', None), *SPECIES.items()]:
        subset = retained if species is None else retained[retained.species.eq(species)]
        inventory[code] = {
            family: int(subset[subset.reviewed_family.eq(family)].sequence_id.nunique())
            for family in FAMILIES
        }
    return inventory


@st.cache_data(show_spinner=False)
def topology_weights(adhesome, signature):
    """Maximum mapped family-pair confidence, with explicit missing-data fallback."""
    from networks import load_network
    supported = adhesome[adhesome.audit_classification.eq('Supported')]
    families = supported.set_index('sequence_id').reviewed_family.to_dict()
    evidence = {key: [] for key, *_ in PAIRS}
    by_species = {}
    for key, code in [('sh','Shae'),('sj','Sjap'),('sm','Sman')]:
        nodes, edges, _ = load_network(code, adhesome)
        sequences = nodes.set_index('identifier').sequence_id.to_dict()
        records = []
        for pair, left, right, fallback in PAIRS:
            matches = []
            for row in edges.itertuples():
                a, b = sequences.get(row.node1_string_id,''), sequences.get(row.node2_string_id,'')
                if {families.get(a),families.get(b)} != {left,right}:
                    continue
                score = float(row.combined_score)
                score = score / 1000 if score > 1 else score
                if not 0 <= score <= 1:
                    raise ValueError('STRING confidence must be normalized to [0,1]')
                matches.append({'sequence_ids':[a,b],'string_ids':[row.node1_string_id,row.node2_string_id],
                                'score':score,'species':code,
                                'source':f'adhesome_network/{code}/{code}_string_interactions.tsv'})
            evidence[pair].extend(matches)
            records.append({'pair':pair,'weight':max(m['score'] for m in matches) if matches else fallback,
                            'basis':'Mapped STRING family association' if matches else 'Framework assumption (no mapped association)',
                            'fallback':not bool(matches),'associations':matches})
        by_species[key] = records
    by_species['pan'] = [
        {'pair':pair,'weight':max(m['score'] for m in evidence[pair]) if evidence[pair] else fallback,
         'basis':'Maximum mapped STRING family association across species' if evidence[pair] else 'Framework assumption (no mapped association)',
         'fallback':not bool(evidence[pair]),'associations':evidence[pair]}
        for pair, _, _, fallback in PAIRS]
    return {'components':['Integrin αβ (β-tail interface)','Talin','Vinculin'],
            'by_species':by_species,'framework':{pair:fallback for pair,_,_,fallback in PAIRS},
            'aggregation':'Maximum combined_score among uniquely mapped supported-family pairs; reference and missing pairs use editable Framework assumptions.',
            'meaning':'Association confidence is a topological input, not a measured affinity or a calibrated recruitment probability.'}


def simulator_html(path: Path, adhesome):
    html = path.read_text(encoding='utf-8')
    html = re.sub(r'const nanoscaleArchitecture = .*?;(?=\n)',
                  lambda _: 'const nanoscaleArchitecture = '+architecture_json()+';',html,count=1)
    if INVENTORY_MARKER not in html:
        raise ValueError(f'{path.name}: audited inventory insertion point is missing')
    payload = json.dumps(supported_inventory(adhesome), ensure_ascii=False).replace('<', '\\u003c')
    if TOPOLOGY_MARKER not in html:
        raise ValueError(f'{path.name}: topology insertion point is missing')
    root = path.parent / 'adhesome_network'
    signature = tuple((p.relative_to(root).as_posix(),p.stat().st_mtime_ns,p.stat().st_size)
                      for p in sorted(root.rglob('*.tsv')))
    topology = json.dumps(topology_weights(adhesome,signature), ensure_ascii=False).replace('<', '\\u003c')
    return html.replace(INVENTORY_MARKER, f'const atlasInventory = {payload};', 1).replace(
        TOPOLOGY_MARKER, f'const atlasTopology = {topology};', 1)
