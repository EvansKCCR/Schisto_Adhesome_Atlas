"""Connect current inventories to explicit conceptual simulation weights."""

import json
from html import escape
import pandas as pd
from pathlib import Path
import streamlit as st
import re


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



def simulator_html(path,adhesome):
    """Use current inventory and explicit conceptual weights, never removed STRING data."""
    html=path.read_text(encoding='utf-8')
    inventory=json.dumps(supported_inventory(adhesome),ensure_ascii=False).replace('<','\\u003c')
    html=html.replace(INVENTORY_MARKER,'const atlasInventory = '+inventory+';')
    html=re.sub(r'speciesLabels=\{.*?\}(?=,pairs=)',lambda _: 'speciesLabels='+json.dumps({'pan':'Pan-schistosome',**SPECIES}),html,count=1)
    # The simulator retains its documented conceptual defaults. Reference row counts
    # and interaction types are not affinities or recruitment probabilities.
    html=html.replace(TOPOLOGY_MARKER,'const atlasTopology = {};')
    html=html.replace('...p,...AdhesionMatrix.defaults,grid:p.grid','...p,...AdhesionMatrix.defaults,...(scenario?.path_controls||{}),grid:p.grid')
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
    return html
