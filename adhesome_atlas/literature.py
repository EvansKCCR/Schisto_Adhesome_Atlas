"""Reconcile published evidence with audited protein IDs and export its provenance."""

from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

import pandas as pd

from data import CANDIDATE_FILE, CANDIDATE_SHEET
from functional_categories import supported_mask
from library_refresh import family_key, reference_family_edges, _write_changed

CROSSWALK = 'files/Schisto_adhesome_focused_literature_crosswalk.xlsx'
DIRECT_LEVELS = {'exact_protein_id', 'published_named_protein'}
SHEETS = ('Schistosoma_studies', 'Library_ID_crosswalk', 'Supported_family_index')
MODEL_DIR = Path('data/literature')
REFERENCE_CONFIG = MODEL_DIR / 'reference_sources.json'
RULE_CONFIG = MODEL_DIR / 'simulator_mechanisms.json'
PMID_URL = 'https://pubmed.ncbi.nlm.nih.gov/'
ORIGINS = {
    'schistosoma_direct_protein', 'schistosoma_family', 'schistosoma_pathway',
    'schistosoma_proteomics', 'metazoan_interaction', 'metazoan_mechanism',
    'computational_family_annotation', 'reference_projected_interaction',
}


def _items(value):
    return [part.strip() for part in str(value).split(';') if part.strip()]


def _records(sheet):
    return enumerate(sheet.fillna('').to_dict('records'), start=2)


def _publication(row, source, row_number):
    rid = row['Ref ID']
    origin, journal, process, pathway = source['crosswalk_context'][rid]
    supplied_pubmed = row['PubMed URL']
    pmid = supplied_pubmed.strip('/').rsplit('/', 1)[-1]
    expected = source['verified_crosswalk_identifiers'].get(rid)
    if expected and row['DOI'].casefold() == expected[0].casefold():
        pmid = source['pubmed_corrections'].get(rid, pmid)
    return dict(
        reference_id=rid, authors=row['First author'], year=int(row['Year']),
        title=row['Verified paper title'], journal=journal, doi=row['DOI'],
        pmid=pmid, source_pubmed_url=supplied_pubmed,
        study_species=['Schistosoma mansoni', 'Schistosoma haematobium', 'Homo sapiens']
        if rid == 'R13' else ['Schistosoma mansoni'],
        studied_protein_or_family=row['Studied protein / family'],
        biological_process=process, experimental_methods=row['Study evidence type'],
        experimental_finding=row['What was shown in Schistosoma'],
        evidence_origin=origin, linked_pathways=[pathway], reference_type='primary study',
        source_crosswalk_sheet=SHEETS[0], source_crosswalk_row=row_number,
    )


def _match_level(strength):
    strength = strength.casefold()
    if 'explicit smp' in strength:
        return 'genomic_candidate_mentioned'
    if 'cross-species' in strength:
        return 'cross_species_family_context'
    if 'pathway' in strength:
        return 'pathway_level'
    if 'accession crosswalk supported' in strength:
        return 'named_locus_context'
    if strength.startswith('direct'):
        return 'published_correspondence_pending'
    return 'family_level'


def named_reference_ids(registry, reference_id):
    """Current accession matches backed by a published locus or named construct."""
    return {link['protein_id'] for link in registry['protein_links']
            if link['reference_id'] == reference_id and link['match_level'] in DIRECT_LEVELS}


def projected_interaction_id(source, target):
    pair = '\x1f'.join(sorted((source, target)))
    return 'P-' + sha256(pair.encode()).hexdigest()[:16]


def references_for_pmids(registry, pmids):
    return sorted({registry['pmid_index'][str(pmid)] for pmid in pmids
                   if str(pmid) in registry['pmid_index']})


def _interaction(iid, a, b, relation, origin, refs, pathway, rule, description, **kwargs):
    return dict(interaction_id=iid, source_component=a, target_component=b,
                source_protein_id='', target_protein_id='', interaction_type=relation,
                molecular_role=pathway.replace('_', ' '), evidence_origin=origin,
                literature_reference_ids=refs, pathway_id=pathway, simulator_rule_id=rule,
                evidence_description=description, is_directed=False,
                is_reference_projected=False, **kwargs)


def _interaction_records(registry, projected):
    rows = [
        _interaction('S01', 'Smβ-Int1', 'SmTK4', 'Reported association',
                     'schistosoma_pathway', ['R01'], 'integrin_reproduction', '',
                     'Association of the cloned β-integrin with the Syk-family kinase.',
                     published_source_locus='Smp_089700'),
        _interaction('S02', 'Smβ-Int1–SmILK–SmPINCH–SmNck2', 'SmVKR1', 'Reconstituted complex',
                     'schistosoma_pathway', ['R02'], 'integrin_vkr1', 'M13',
                     'Co-expression, co-immunoprecipitation and perturbations support a multicomponent complex.'),
        _interaction('sm:ilk-pinch', 'SmILK', 'SmPINCH', 'Complex association',
                     'schistosoma_pathway', ['R02'], 'integrin_vkr1', 'M09',
                     'Deletion analyses and co-immunoprecipitation interrogated ILK and PINCH in the reconstituted complex.',
                     source_locus='Sman__Smp_079760', target_locus='Sman__Smp_020540'),
        _interaction('sm:pinch-nck', 'SmPINCH', 'SmNck2', 'Complex association',
                     'schistosoma_pathway', ['R02'], 'integrin_vkr1', 'M12',
                     'The PINCH LIM4 and Nck2 SH3 regions contributed to reconstituted complex signalling.',
                     source_locus='Sman__Smp_020540', target_locus='Sman__Smp_014850'),
        _interaction('sm:nck-vkr', 'SmNck2', 'SmVKR1', 'Multicomponent pathway context',
                     'schistosoma_pathway', ['R02'], 'integrin_vkr1', 'M13',
                     'The multicomponent receptor complex supported SmVKR1 phosphorylation.',
                     source_locus='Sman__Smp_014850'),
        _interaction('S03', 'SmDia', 'SmTK3', 'Reported association', 'schistosoma_pathway',
                     ['R05'], 'src_rho_actin', 'M17', 'Formin–Src association examined in interaction assays.'),
        _interaction('S04', 'SmDia', 'SmRho1', 'Reported association', 'schistosoma_pathway',
                     ['R05'], 'src_rho_actin', 'M17', 'Formin–Rho association examined in interaction assays.'),
        _interaction('S05', 'SmTK6', 'SmTK3', 'Reported association', 'schistosoma_pathway',
                     ['R06'], 'gonadal_kinases', 'M17', 'Hybrid kinase association studied with named constructs.'),
        _interaction('S06', 'SmTK6', 'SmVKR1', 'Reported association', 'schistosoma_pathway',
                     ['R06'], 'gonadal_kinases', '', 'Hybrid kinase association studied with named constructs.'),
        _interaction('C01', 'Talin', 'Vinculin', 'Force-sensitive binding', 'metazoan_mechanism',
                     ['R16'], 'talin_vinculin_clutch', 'M05', 'Mechanical exposure of talin binding sites.'),
        _interaction('C02', 'Kindlin-2', 'ILK–PINCH–parvin', 'Complex binding', 'metazoan_interaction',
                     ['R17', 'R18', 'R19'], 'kindlin_ipp', 'M10', 'The kindlin-2 F2 subdomain associates with IPP.'),
        _interaction('C03', 'Kindlin-2', 'Paxillin', 'Binding and recruitment', 'metazoan_interaction',
                     ['R20'], 'layered_adhesion', 'M15', 'Paxillin binding examined in reconstituted and cellular assays.'),
        _interaction('C04', 'FAK', 'Src', 'Phosphorylation-dependent association', 'metazoan_interaction',
                     ['R21'], 'fak_src', 'M14', 'FAK Tyr397 supports Src SH2-dependent association.'),
    ]
    if 'Sman__Smp_089700' in named_reference_ids(registry, 'R01'):
        rows[0]['source_protein_id'] = 'Sman__Smp_089700'
    for rule in registry['mechanisms']['rules']:
        rows.append({
            **_interaction(rule['rule_id'], rule['components'][0], ' · '.join(rule['components'][1:]),
                           'Simulated state transition', rule['evidence_origin'], rule['reference_ids'],
                           rule['functional_layer'], rule['rule_id'], rule['transition_condition']),
            'is_directed': True,
        })
    for row in projected.itertuples():
        pmids = _items(row.PMIDs)
        rows.append({
            **_interaction(projected_interaction_id(row.family_A, row.family_B), row.family_A, row.family_B,
                           'Reference-family projected association', 'reference_projected_interaction',
                           references_for_pmids(registry, pmids), 'reference_family_projection', '',
                           row.evidence_interpretation, source_pmids=pmids, reference_symbols=row.human_symbol_pairs,
                           reference_sources=row.data_sources),
            'is_reference_projected': True,
        })
    for row in rows:
        for endpoint in ('source','target'):
            locus=row.pop(endpoint+'_locus','')
            if locus and locus in named_reference_ids(registry,'R02'):
                row[endpoint+'_protein_id']=locus
        refs = [registry['references'][rid] for rid in row['literature_reference_ids']]
        row['doi_urls'] = [ref['doi_url'] for ref in refs]
        row['study_species'] = sorted({species for ref in refs for species in ref['study_species']})
        row['experimental_methods'] = sorted({ref['experimental_methods'] for ref in refs})
    return rows


def build_registry(root, candidates, sheets=None):
    root = Path(root)
    source = json.loads((root / REFERENCE_CONFIG).read_text(encoding='utf-8'))
    mechanisms = json.loads((root / RULE_CONFIG).read_text(encoding='utf-8'))
    sheets = pd.read_excel(root / CROSSWALK, sheet_name=None) if sheets is None else sheets
    missing = set(SHEETS) - set(sheets)
    if missing:
        raise ValueError('Literature crosswalk is missing worksheets: ' + ', '.join(sorted(missing)))
    refs = [_publication(row, source, n) for n, row in _records(sheets[SHEETS[0]])]
    if {ref['reference_id'] for ref in refs} != set(source['crosswalk_context']):
        raise ValueError('Crosswalk references must retain R01–R14.')
    refs += [{**ref, 'source_crosswalk_sheet': '', 'source_crosswalk_row': None}
             for ref in source['additional_references']]
    if len({r['reference_id'] for r in refs}) != len(refs) or len({r['doi'].lower() for r in refs}) != len(refs):
        raise ValueError('Duplicate reference ID or DOI in the literature registry.')
    verified = set()
    for ref in refs:
        rid = ref['reference_id']
        expected = source['verified_crosswalk_identifiers'].get(rid)
        if not ref['source_crosswalk_sheet'] or (
            expected and ref['doi'].casefold() == expected[0].casefold() and ref['pmid'] == expected[1]
        ):
            verified.add(rid)

    candidates = candidates.fillna('').drop_duplicates('sequence_id')
    records = candidates.set_index('sequence_id').to_dict('index')
    aliases = defaultdict(list)
    for pid in records:
        aliases[pid.split('__', 1)[-1]].append(pid)
    published = {(ref, pid): (name, locus, accession, level)
                 for ref, pid, name, locus, accession, level in source['published_loci'] if ref in verified}
    links, mapping_audit = [], []
    for n, row in _records(sheets[SHEETS[1]]):
        original = row['Library protein ID']
        matches = [original] if original in records else aliases.get(original, [])
        pid = matches[0] if len(matches) == 1 else ''
        record = records.get(pid, {})
        changes = [field for field, old, new in [
            ('family', row['Library family'], record.get('family')),
            ('orthogroup', row['Orthogroup'], record.get('orthogroup')),
            ('grade', row['Grade'], record.get('grade')),
            ('support', row['Family support'], record.get('family_support_level')),
        ] if pid and old != new]
        status = ('exact' if pid == original else 'unique_accession') if pid else ('ambiguous' if matches else 'missing')
        audit = dict(source_protein_id=original, protein_id=pid, mapping_status=status, changes=changes,
                     source_family=row['Library family'], current_family=record.get('family', ''),
                     source_grade=row['Grade'], current_grade=record.get('grade', ''),
                     source_support=row['Family support'], current_support=record.get('family_support_level', ''),
                     source_orthogroup=row['Orthogroup'], current_orthogroup=record.get('orthogroup', ''),
                     source_crosswalk_sheet=SHEETS[1], source_crosswalk_row=n,
                     original_match=row['Literature match strength'], original_note=row['Copy-ready scientific annotation note'],
                     reference_ids=_items(row['Reference IDs']))
        mapping_audit.append(audit)
        for rid in audit['reference_ids']:
            level = _match_level(audit['original_match'])
            if 'family' in changes and family_key(audit['source_family']) != family_key(audit['current_family']):
                if level == 'family_level':
                    level = 'source_family_changed'
            link = {**audit, 'reference_id':rid, 'match_level':level, 'assayed_identity':False,
                    'note':audit['original_note']}
            if (rid, pid) in published:
                name, locus, accession, level = published[rid, pid]
                link.update(match_level=level, assayed_identity=True, published_name=name,
                            published_locus=locus, published_accession=accession,
                            note=f'{name} is reported at {locus}. The current catalogue assignment and sequence model are shown separately.')
            links.append(link)
    for (rid, pid), (name, locus, accession, level) in published.items():
        if any(link['protein_id'] == pid and link['reference_id'] == rid for link in links):
            continue
        record = records.get(pid, {})
        links.append(dict(reference_id=rid, source_protein_id=pid, protein_id=pid if record else '',
                          mapping_status='exact' if record else 'missing', match_level=level,
                          assayed_identity=bool(record), current_family=record.get('family', ''),
                          current_orthogroup=record.get('orthogroup', ''),
                          published_name=name, published_locus=locus, published_accession=accession,
                          source_crosswalk_sheet='', source_crosswalk_row=None,
                          note=f'The paper reports {name} transcript {locus}. The Atlas ID is a locus-level correspondence.'))

    family_rows = []
    for n, row in _records(sheets[SHEETS[2]]):
        family = row['Library family label']
        group = candidates[candidates.family.map(family_key).eq(family_key(family))]
        supported = group[supported_mask(group)]
        examples = _items(row['Examples from S. mansoni'])
        family_rows.append(dict(source_family=family, family_labels=sorted(set(group.family)),
                                reference_ids=_items(row['Relevant references']), interpretation=row['Interpretation'],
                                source_count=int(row['Current unique proteins']), current_count=len(supported),
                                source_orthogroups=int(row['Distinct orthogroups']),
                                current_orthogroups=supported.loc[supported.orthogroup.ne(''), 'orthogroup'].nunique(),
                                source_examples=examples, missing_examples=sorted(set(examples) - records.keys()),
                                source_crosswalk_sheet=SHEETS[2], source_crosswalk_row=n))
    for ref in refs:
        ref['doi_url'] = 'https://doi.org/' + ref['doi']
        ref['pubmed_url'] = PMID_URL + ref['pmid'] + '/'
        rid = ref['reference_id']
        ref['reference_verification_status'] = 'bibliography_verified' if rid in verified else 'unverified'
        ref['verification_source'] = ref['pubmed_url'] if rid in verified else ''
        ref['verification_date'] = source['verified_on'] if rid in verified else ''
        attached = [link for link in links if link['reference_id'] == rid and link['protein_id']
                    and link['match_level'] != 'source_family_changed']
        ref['linked_library_protein_ids'] = sorted({link['protein_id'] for link in attached})
        families = {link['current_family'] for link in attached if link['current_family']}
        families.update(label for row in family_rows if rid in row['reference_ids'] for label in row['family_labels'])
        keys = {family_key(name) for name in ref.pop('families', [])}
        families.update(label for label in candidates.family.unique() if family_key(label) in keys)
        ref['linked_family_labels'] = sorted(families)
        ref['linked_orthogroups'] = sorted({link['current_orthogroup'] for link in attached if link['current_orthogroup']})
        ref['linked_simulator_interactions'] = [rule['rule_id'] for rule in mechanisms['rules'] if rid in rule['reference_ids']]
        ref['evidence_level'] = ('general_metazoan_mechanism' if rid not in source['crosswalk_context']
                                 else 'curated_study_with_scoped_links')
    reference_index = {ref['reference_id']:ref for ref in refs}
    used_ids = {link['reference_id'] for link in links}
    used_ids.update(rid for row in [*family_rows, *mechanisms['rules'], *mechanisms['layers']]
                    for rid in row['reference_ids'])
    if used_ids - reference_index.keys():
        raise ValueError('Unknown reference IDs: ' + ', '.join(sorted(used_ids - reference_index.keys())))
    for rule in mechanisms['rules']:
        supporting = [reference_index[rid] for rid in rule['reference_ids']]
        rule['doi_urls'] = [ref['doi_url'] for ref in supporting]
        rule['study_species'] = sorted({species for ref in supporting for species in ref['study_species']})
    inputs = {str(path).replace('\\', '/'):sha256((root / path).read_bytes()).hexdigest()
              for path in [CANDIDATE_FILE, CROSSWALK, REFERENCE_CONFIG, RULE_CONFIG,
                           'adhesome_network/interactions.csv',
                           'adhesome_network/Schistosome_human_gene_family_crosswalk.csv',
                           'Target_prioritization.md']}
    registry = dict(version=source['version'], references=reference_index, protein_links=links,
                    mapping_audit=mapping_audit, family_index=family_rows, mechanisms=mechanisms,
                    pmid_index={ref['pmid']:ref['reference_id'] for ref in refs if ref['reference_id'] in verified},
                    provenance=dict(atlas_build_version='atlas-data-6', registry_version=source['version'],
                                    simulator_config_version=mechanisms['version'], protein_id_mapping_date=source['verified_on'],
                                    candidate_sheet=CANDIDATE_SHEET, literature_sheets=list(SHEETS),
                                    unique_proteins=len(records), source_reference_count=len(sheets[SHEETS[0]]),
                                    source_mapping_count=len(mapping_audit), source_family_count=len(family_rows),
                                    doi_verification={ref['reference_id']:ref['reference_verification_status'] for ref in refs},
                                    support_counts=candidates.support_category.value_counts().to_dict(),
                                    inputs=inputs))
    registry['interactions'] = _interaction_records(registry, reference_family_edges(root))
    return registry


def evidence_for(registry, family, protein_id=''):
    """Return explicitly scoped accession links and separate family-context links."""
    if not registry:
        return []
    direct_links = [link for link in registry['protein_links'] if protein_id and link['protein_id'] == protein_id]
    seen = {link['reference_id'] for link in direct_links}
    key = family_key(family)
    context = []
    for ref in registry['references'].values():
        rid = ref['reference_id']
        if rid in seen or key not in {family_key(label) for label in ref['linked_family_labels']}:
            continue
        indexed = next((row for row in registry['family_index'] if rid in row['reference_ids']
                        and key == family_key(row['source_family'])), {})
        scope = 'general_metazoan_mechanism' if ref['evidence_origin'].startswith('metazoan') else 'family_level'
        if 'pathway context' in indexed.get('interpretation', '').lower().replace('-', ' '):
            scope = 'pathway_level'
        context.append(dict(reference_id=rid, match_level=scope, assayed_identity=False,
                            note=indexed.get('interpretation', 'Biological context for this family.')))
    return direct_links + context


def browser_evidence(registry, candidates):
    """Compact evidence payload for the offline map, dossiers and inspectors."""
    if not registry:
        return {'references':{}, 'protein_links':{}, 'family_links':{}, 'pmid_index':{}}
    protein_links = defaultdict(list)
    for link in registry['protein_links']:
        if link['protein_id']:
            protein_links[link['protein_id']].append({key:link[key] for key in
                ['reference_id', 'match_level', 'note', 'assayed_identity']})
    return {
        'references':registry['references'],
        'pmid_index':registry['pmid_index'],
        'protein_links':dict(protein_links),
        'family_links':{family:evidence_for(registry, family) for family in candidates.family.unique()},
    }


def browser_script():
    """Render literature evidence without a separate deployment asset."""
    return """/* Render structured study references in standalone Atlas documents. */
function renderLiteratureEvidence(parent, links, references) {
    for (const link of links) {
        const ref = references[link.reference_id];
        if (!ref) continue;
        const item = document.createElement('div');
        item.className = 'atlas-literature-record';
        const heading = document.createElement('strong');
        heading.textContent = ref.reference_id + ' · ' + ref.authors + ' (' + ref.year + ') · ' + ref.title;
        const scope = document.createElement('p');
        scope.textContent = [link.match_level, ref.evidence_origin, ref.study_species.join(', ')]
            .filter(Boolean).join(' · ').replaceAll('_', ' ');
        if (ref.reference_verification_status === 'unverified') scope.textContent += ' · Bibliography unverified';
        const finding = document.createElement('p');
        finding.textContent = [ref.experimental_methods, ref.experimental_finding, link.note].filter(Boolean).join(' · ');
        item.append(heading, scope, finding);
        for (const [label, url] of [['DOI', ref.doi_url], ['PubMed', ref.pubmed_url]]) {
            if (!url) continue;
            const anchor = document.createElement('a');
            anchor.textContent = label;
            anchor.href = url;
            anchor.target = '_blank';
            anchor.rel = 'noopener';
            item.append(anchor, document.createTextNode(' '));
        }
        parent.appendChild(item);
    }
}
"""


def tsv(records):
    def cell(value):
        return json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
    return pd.DataFrame([{key:cell(value) for key, value in row.items()} for row in records]).to_csv(
        sep='\t', index=False, lineterminator='\n')


def registry_exports(registry):
    refs=registry['references'].values()
    return {
        'literature_registry.json': json.dumps(registry, ensure_ascii=False, indent=2) + '\n',
        'literature_references.tsv': tsv(refs),
        'protein_to_reference.tsv': tsv(registry['protein_links']),
        'protein_mapping_audit.tsv': tsv(registry['mapping_audit']),
        'family_evidence.tsv': tsv(registry['family_index']),
        'family_to_reference.tsv': tsv(
            dict(family=family, reference_id=ref['reference_id'], evidence_origin=ref['evidence_origin'],
                 doi_url=ref['doi_url'], relationship=link['match_level'])
            for family in sorted({name for ref in refs for name in ref['linked_family_labels']})
            for link in evidence_for(registry,family)
            for ref in [registry['references'][link['reference_id']]]
        ),
        'pathway_to_reference.tsv': tsv(
            dict(pathway_id=pathway,reference_id=ref['reference_id'],evidence_origin=ref['evidence_origin'],
                 biological_process=ref['biological_process'],doi_url=ref['doi_url'])
            for ref in refs for pathway in ref['linked_pathways']
        ),
        'interaction_evidence.tsv': tsv(registry['interactions']),
        'simulator_rule_to_reference.tsv': tsv(registry['mechanisms']['rules']),
        'provenance.json': json.dumps(registry['provenance'], ensure_ascii=False, indent=2) + '\n',
    }


def write_registry(root, registry):
    for name, contents in registry_exports(registry).items():
        _write_changed(Path(root) / MODEL_DIR / name, contents)
