"""Refresh the supplied family map from the audited workbook and published complex evidence."""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
HTML = ROOT / 'Schistosome_adhesome_interactive.html'
BOOK = ROOT / 'files' / 'adhesome_candidates_list.xlsx'
PAPER = 'Gelmedin et al. 2017, PLOS Pathogens, doi:10.1371/journal.ppat.1006147'


def replace_array(html, name, values):
    return re.sub(rf'const {name}=\[.*?\];',
                  lambda _: f'const {name}=' + json.dumps(values, ensure_ascii=False) + ';',
                  html, count=1, flags=re.S)


def main():
    html = HTML.read_text(encoding='utf-8')
    nodes = json.loads(re.search(r'const nodes=(\[.*?\]);', html, re.S).group(1))
    edges = json.loads(re.search(r'const edges=(\[.*?\]);', html, re.S).group(1))
    audited = pd.read_excel(BOOK, sheet_name='Audited_family_assignment')
    retained = audited[audited.audit_family.ne('unassigned')]
    species = ['S. haematobium', 'S. japonicum', 'S. mansoni']
    counts = retained.groupby(['audit_family', 'Specie']).protein_id.nunique()
    for node in nodes:
        family = node.get('family')
        if family:
            node['count'] = ' / '.join(str(int(counts.get((family, sp), 0))) for sp in species)
    if not any(node['id'] == 'integrin_ab' for node in nodes):
        nodes.append(dict(id='integrin_ab', x=542, y=159, w=96, h=44,
                          title='αβ receptor', count='', color='#b91c1c',
                          status='libraryOnly', layer='Plasma membrane',
                          detail='Family-level integrin αβ heterodimer. Exact subunit pairing is unresolved.'))
    for edge in edges:
        if edge['a'] in {'collagen', 'laminin'} and edge['b'] == 'inta':
            edge['b'] = 'integrin_ab'
            edge['relation'] = 'putative ligand–αβ heterodimer recognition'
            edge['interpretation'] = 'Candidate extracellular ligand class connected to the integrin αβ receptor; individual ligand binding and subunit specificity remain to be tested.'
            edge['class'] = 'ligand'
        elif edge['a'] == 'inta' and edge['b'] == 'intb':
            edge.update(a='integrin_ab', b='inta', relation='α constituent of heterodimer')
        elif edge['a'] == 'pinch' and edge['b'] == 'ilk':
            edge.update(evidence_class='experimentally supported S. mansoni complex',
                        reference=PAPER,
                        transfer_basis='SmILK–SmPINCH–SmNck2 assembly tested by co-expression, co-immunoprecipitation and deletion constructs in Xenopus oocytes',
                        species_support='S. mansoni: Smp_079760 (ILK), Smp_020540.2 (PINCH), Smp_014850 (Nck2)',
                        interpretation='Experimental support for participation in the SmILK–SmPINCH–SmNck2 complex; not evidence that every family member forms the same complex.')
    if not any(e['a'] == 'integrin_ab' and e['b'] == 'intb' for e in edges):
        alpha = next(e for e in edges if e['a'] == 'integrin_ab' and e['b'] == 'inta')
        edges.insert(edges.index(alpha)+1, {**alpha, 'b': 'intb', 'relation': 'β constituent of heterodimer'})
    if not any({e['a'], e['b']} == {'pinch', 'nck'} for e in edges):
        edges.append(dict(a='pinch', b='nck', kind='direct',
                          relation='SmPINCH–SmNck2 association in the ILK–PINCH–Nck2 complex',
                          evidence_class='experimentally supported S. mansoni complex', reference=PAPER,
                          transfer_basis='Co-expression, co-immunoprecipitation and domain deletion analysis in Xenopus oocytes',
                          species_support='S. mansoni: Smp_020540.2 (PINCH), Smp_014850 (Nck2), Smp_079760 (ILK)',
                          interpretation='Experimentally supported complex association in the heterologous system; family-wide and endogenous assembly remain separate questions.',
                          directional=False))
    html = replace_array(replace_array(html, 'nodes', nodes), 'edges', edges)
    html = html.replace('Shc, Grb2, Nck and profilin are displayed but their edges are not inferred.',
                        'Shc, Grb2 and profilin have no curated edges. The PINCH–Nck2 association is supported by Gelmedin et al. (2017) for S. mansoni.')
    html = html.replace('Established/reference complex relationship', 'Established reference or experimentally supported complex')
    HTML.write_text(html, encoding='utf-8')


if __name__ == '__main__':
    main()
