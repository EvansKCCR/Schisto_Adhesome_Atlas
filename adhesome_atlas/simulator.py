"""Embed the standalone qualitative simulator with current audited family counts."""

import json
from pathlib import Path


SIMULATOR_FILE = 'schistosome_integrin_adhesome_hypothesis_simulator.html'
INVENTORY_MARKER = 'const atlasInventory = {};'
FAMILIES = ('integrin_alpha', 'integrin_beta', 'FAK', 'Src')
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


def simulator_html(path: Path, adhesome):
    html = path.read_text(encoding='utf-8')
    if INVENTORY_MARKER not in html:
        raise ValueError(f'{path.name}: audited inventory insertion point is missing')
    payload = json.dumps(supported_inventory(adhesome), ensure_ascii=False).replace('<', '\\u003c')
    return html.replace(INVENTORY_MARKER, f'const atlasInventory = {payload};', 1)
