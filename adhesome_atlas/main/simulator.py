"""Connect current inventories to explicit conceptual simulation weights."""

import json
from html import escape
import pandas as pd
from pathlib import Path
import re
from design_system import network_style
from library_refresh import family_key
from functional_categories import supported_mask
from literature import browser_script


SIMULATOR_FILE = 'adhesome_network/schistosome_integrin_adhesome_hypothesis_simulator.html'
INVENTORY_MARKER = 'const atlasInventory = {};'
TOPOLOGY_MARKER = 'const atlasTopology = {};'
FAMILIES = ('integrin_alpha', 'integrin_beta', 'talin', 'vinculin', 'FAK', 'Src')
PAIRS = [('IT','integrin_beta','talin',.85),('TV','talin','vinculin',.30),
         ('IV','integrin_beta','vinculin',.05)]
SPECIES = {
    'sb': 'Schistosoma bovis',
    'sc': 'Schistosoma curassoni',
    'si': 'Schistosoma intercalatum',
    'sr': 'Schistosoma rodhaini',
    'sh': 'Schistosoma haematobium',
    'sj': 'Schistosoma japonicum',
    'sm': 'Schistosoma mansoni',
}


class SimulatorAssetsError(ValueError):
    """The deployed simulator HTML needs to be regenerated."""


def supported_inventory(adhesome):
    """Count distinct supported proteins, without transferring reference counts."""
    if 'family_support_level' not in adhesome and 'grade' not in adhesome:
        retained = adhesome[adhesome.audit_classification.eq('Supported')]
    else:
        retained = adhesome[supported_mask(adhesome)]
    inventory = {}
    for code, species in [('pan', None), *SPECIES.items()]:
        subset = retained if species is None else retained[retained.species.eq(species)]
        families=subset.reviewed_family.map(family_key)
        inventory[code] = {
            family: int(subset[families.eq(family_key(family))].sequence_id.nunique())
            for family in FAMILIES
        }
    return inventory



def refresh_simulator_assets(html,adhesome,literature):
    """Embed current rule metadata and engine source for offline and live use."""
    source=Path(__file__).resolve().parent
    retained=adhesome[supported_mask(adhesome)].drop_duplicates('sequence_id')
    fields=['sequence_id','species','family','family_support_level']
    families=retained.family.map(family_key)
    components=sorted({name for rule in literature['mechanisms']['rules'] for name in rule['components']})
    candidates={}
    for component in components:
        keys={family_key(component)}
        if component=='actin':
            keys.add('actin conventional')
        candidates[component]=json.loads(retained.loc[families.isin(keys),fields].to_json(orient='records'))
    payload=dict(mechanisms=literature['mechanisms'],references=literature['references'],
                 candidates=candidates,provenance=literature['provenance'])
    scripts={}
    for marker in ('matrix-engine','atlas-mechanism-ui','atlas-mechanisms'):
        match=re.search(rf"<script\b[^>]*\bid=['\"]{marker}['\"][^>]*>(.*?)</script>",html,flags=re.S)
        if match is None:
            raise SimulatorAssetsError('Missing simulator asset marker: '+marker)
        scripts[marker]=match
    try:
        engine=(source/'simulator_engine.js').read_text(encoding='utf-8')
        controls=(source/'simulator_evidence.js').read_text(encoding='utf-8')
    except FileNotFoundError as error:
        # Keep the engine and its UI together when using the offline bundle.
        try:
            embedded_version=json.loads(scripts['atlas-mechanisms'][1])['mechanisms']['version']
        except (ValueError,KeyError,TypeError) as metadata_error:
            raise SimulatorAssetsError('Embedded simulator metadata is incomplete.') from metadata_error
        if embedded_version!=payload['mechanisms']['version'] or any(
            not scripts[marker][1].strip() for marker in ('matrix-engine','atlas-mechanism-ui')
        ):
            raise SimulatorAssetsError('Embedded simulator scripts are missing or out of date.') from error
        assets={}
    else:
        assets={'matrix-engine':engine,'atlas-mechanism-ui':browser_script()+'\n'+controls}
    assets['atlas-mechanisms']=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    for marker in sorted(assets,key=lambda key:scripts[key].start(1),reverse=True):
        start,end=scripts[marker].span(1)
        html=html[:start]+'\n'+assets[marker]+'\n'+html[end:]
    return html


def simulator_html(path,adhesome,literature=None):
    """Use current inventory and explicit conceptual weights, never removed STRING data."""
    html=path.read_text(encoding='utf-8')
    if literature:
        html=refresh_simulator_assets(html,adhesome,literature)
    inventory=json.dumps(supported_inventory(adhesome),ensure_ascii=False).replace('<','\\u003c')
    html=re.sub(r'const atlasInventory = \{[^\n]*\};',lambda _: 'const atlasInventory = '+inventory+';',html,count=1)
    html=re.sub(r'speciesLabels=\{.*?\}(?=,pairs=)',lambda _: 'speciesLabels='+json.dumps({'pan':'Pan-schistosome',**SPECIES}),html,count=1)
    # The simulator retains its documented conceptual defaults. Reference row counts
    # and interaction types are not affinities or recruitment probabilities.
    html=html.replace(TOPOLOGY_MARKER,'const atlasTopology = {};')
    options="<option value='pan'>Pan-schistosome</option>"+''.join("<option value='"+key+"'>"+escape(name)+"</option>" for key,name in SPECIES.items())
    html=re.sub(r"(<select id=['\"]species['\"]>).*?(</select>)",lambda m:m[1]+options+m[2],html,count=1,flags=re.S)
    source=path.parent.parent/'orthology/adhesome_candidates_list/direct_orthologues.tsv'
    if source.exists():
        refs=sorted(pd.read_csv(source,sep='\t',usecols=['reference_species']).reference_species.dropna().unique())
        html=re.sub(r"(<select id=['\"]referenceSpecies['\"]>).*?(</select>)",lambda m:m[1]+''.join('<option'+(' selected' if name=='Homo sapiens' else '')+'>'+escape(name)+'</option>' for name in refs)+m[2],html,count=1,flags=re.S)
    html=html.replace('Mapped STRING + explicit fallbacks','Conceptual baseline weights')
    html=html.replace('STRING confidence supplies editable topology weights','Editable conceptual assumptions supply topology weights')
    html=html.replace('No mapped association','No binding-weight measurement in the current library')
    html=html.replace('Mapped STRING confidence','Conceptual recruitment weight')
    html=html.replace('mapped intracellular associations use the integrin β family','the intracellular interface represents the integrin β tail')
    species_map=json.dumps({**{name:key for key,name in SPECIES.items()},'S. haematobium':'sh','S. japonicum':'sj','S. mansoni':'sm'})
    html=html.replace("value.species==='S. haematobium'?'sh':value.species==='S. japonicum'?'sj':value.species==='S. mansoni'||value.node==='vkr1'?'sm':'pan'","("+species_map+")[value.species]||(value.node==='vkr1'?'sm':'pan')")
    html=html.replace("$('referenceSpecies').value='H. sapiens'","$('referenceSpecies').value='Homo sapiens'")
    html=re.sub(r'<!-- ATLAS_SIM_STYLE_START -->.*?<!-- ATLAS_SIM_STYLE_END -->','',html,flags=re.S)
    return html.replace('</head>','<!-- ATLAS_SIM_STYLE_START -->'+network_style()+'''<style>
body{background:#f1f6f2;padding:14px;font-family:var(--atlas-font)}.app{max-width:none}
header,.panel,details{border:1px solid var(--atlas-line);border-radius:14px;box-shadow:none}
header{border-top:3px solid var(--atlas-violet);padding:20px}h1{font-size:23px;letter-spacing:-.035em}h2{font-size:19px;letter-spacing:-.025em}
.muted{line-height:1.6}.note,#linkedContext{background:#f8f5e9;border-color:#d6c58e;border-radius:10px}
.zoneCard,.moduleCard{border-color:var(--atlas-line);border-radius:10px}
.metrics span{background:var(--atlas-tint)}.reference{border-top-color:var(--atlas-accent)}button{border-width:1px}
</style><!-- ATLAS_SIM_STYLE_END --></head>''',1)
