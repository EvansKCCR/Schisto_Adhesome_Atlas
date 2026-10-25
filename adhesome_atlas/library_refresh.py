"""Rebuild derived networks from primary sources without editing scientific annotations."""
from collections import Counter,defaultdict
from functools import lru_cache
from io import BytesIO
from itertools import product
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import pandas as pd

VERSION='library-refresh-1'
EDGE_FILE='Schistosome_human_reference_family_edges.csv'
INVENTORY_FILE='Schistosome_adhesome_family_inventory.csv'
MEMBERS_FILE='Schistosome_adhesome_candidate_node_members.csv'
MODULE_FILE='family_module_annotations.csv'
DERIVED_FILES={EDGE_FILE,INVENTORY_FILE,MEMBERS_FILE}
UNRESOLVED='Unassigned / unresolved families'
EDGE_COLUMNS=['family_A','family_B','human_reference_pairs','original_rows','human_symbol_pairs',
    'interaction_types','effects','PMIDs','data_sources','evidence_interpretation']


def _csv(data):
    return pd.read_csv(BytesIO(data),dtype=str,keep_default_na=False)


def _required(frame,columns,label):
    missing=set(columns)-set(frame)
    if missing:raise ValueError(label+' is missing required columns: '+', '.join(sorted(missing)))


def _aggregate(raw,crosswalk):
    _required(raw,['Source','Target','Effect','Type','PMID','data_source'],'interactions.csv')
    _required(crosswalk,['human_symbol','candidate_family'],'Family crosswalk')
    mapping=defaultdict(set)
    for row in crosswalk.itertuples():
        if row.human_symbol.strip() and row.candidate_family.strip():
            if row.candidate_family.strip().casefold() in {'unassigned','unresolved'}:
                raise ValueError('The crosswalk must not assign human interactions to an unassigned candidate pool.')
            mapping[row.human_symbol.strip()].add(row.candidate_family.strip())
    groups={};mapped_rows=0;intra=set();unmapped=Counter()
    for row in raw.to_dict('records'):
        a,b=row['Source'].strip(),row['Target'].strip()
        for symbol in {a,b}-set(mapping):unmapped[symbol]+=1
        if not mapping.get(a) or not mapping.get(b):continue
        mapped_rows+=1
        for fa,fb in product(sorted(mapping[a]),sorted(mapping[b])):
            if fa==fb:intra.add(fa);continue
            key=tuple(sorted((fa,fb)))
            item=groups.setdefault(key,dict(pairs=set(),symbols=set(),types=Counter(),effects=Counter(),pmids=set(),sources=set(),rows=0))
            item['rows']+=1;item['pairs'].add(tuple(sorted((a,b))));item['symbols'].add(a+' — '+b)
            item['types'][row['Type']]+=1;item['effects'][row['Effect']]+=1
            item['pmids'].update(re.findall(r'\d+',row['PMID']))
            if row['data_source']:item['sources'].add(row['data_source'])
    result=[]
    for (a,b),item in sorted(groups.items()):
        result.append(dict(family_A=a,family_B=b,human_reference_pairs=len(item['pairs']),original_rows=item['rows'],
            human_symbol_pairs='; '.join(sorted(item['symbols'])),interaction_types=json.dumps(dict(sorted(item['types'].items()))),
            effects=json.dumps(dict(sorted(item['effects'].items()))),PMIDs='; '.join(sorted(item['pmids'],key=int)),
            data_sources='; '.join(sorted(item['sources'])),
            evidence_interpretation='Metazoan reference transferred through the curated family crosswalk; parasite binding partners remain unresolved'))
    diagnostics=dict(reference_rows=len(raw),mapped_rows=mapped_rows,interfamily_edges=len(result),intrafamily_groups=len(intra),
        distinct_reference_symbols=len(set(raw.Source)|set(raw.Target)),matched_symbols=len((set(raw.Source)|set(raw.Target))&set(mapping)),
        unmapped_symbols=[dict(symbol=s,rows=n) for s,n in sorted(unmapped.items())])
    return pd.DataFrame(result,columns=EDGE_COLUMNS),diagnostics


@lru_cache(maxsize=4)
def _cached_reference(raw_bytes,crosswalk_bytes):
    return _aggregate(_csv(raw_bytes),_csv(crosswalk_bytes))


def reference_family_edges(root):
    net=Path(root)/'adhesome_network'
    edges,_=_cached_reference((net/'interactions.csv').read_bytes(),(net/'Schistosome_human_gene_family_crosswalk.csv').read_bytes())
    return edges.copy(deep=True)


def module_annotations(root):
    net=Path(root)/'adhesome_network';path=net/MODULE_FILE
    # Backwards-compatible first launch; the separate editable mapping avoids a
    # circular dependency between regenerated inventory counts and module annotations.
    if not path.exists():path=net/INVENTORY_FILE
    if not path.exists():return {}
    annotations=pd.read_csv(path,dtype=str).fillna('')
    _required(annotations,['family','visual_group'],path.name)
    if annotations.family.duplicated().any():raise ValueError('Module annotations contain duplicate family keys.')
    return dict(zip(annotations.family,annotations.visual_group))


def _write_changed(path,body):
    """Atomic replacement, no write/mtime changes when contents already agree."""
    encoded=body.encode('utf-8')
    if path.exists() and path.read_bytes()==encoded:return False
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(encoded)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return True


def refresh_derived(candidates,root,persist=True):
    """One coherent in-memory snapshot; disk mirrors are optional on read-only hosts."""
    root=Path(root);net=root/'adhesome_network'
    raw_bytes=(net/'interactions.csv').read_bytes();cross_bytes=(net/'Schistosome_human_gene_family_crosswalk.csv').read_bytes()
    edges,diagnostics=_cached_reference(raw_bytes,cross_bytes)
    crosswalk=_csv(cross_bytes);groups=module_annotations(root);species=sorted(candidates.species.unique());inventory=[]
    symbol_map=crosswalk.groupby('candidate_family').human_symbol.agg(lambda s:';'.join(sorted(set(s)))).to_dict()
    for family,group in candidates.groupby('family',sort=True):
        row=dict(family=family,visual_group=groups.get(family) or UNRESOLVED,total=group.sequence_id.nunique(),
            **{'grade_'+grade:group.loc[group.grade.eq(grade),'sequence_id'].nunique() for grade in ['A','B','C','D']},
            human_mapping_symbols=symbol_map.get(family,''))
        row.update({name:group.loc[group.species.eq(name),'sequence_id'].nunique() for name in species});inventory.append(row)
    inventory=pd.DataFrame(inventory)
    members=candidates[['species','sequence_id','family','grade','assignment_confidence','family_decision','architecture']].rename(
        columns={'sequence_id':'protein_id','family':'putative_audited_family','architecture':'Pfam_architecture'})
    primary=[root/'files/adhesome_candidates_list.xlsx',net/'interactions.csv',net/'Schistosome_human_gene_family_crosswalk.csv']
    if (net/MODULE_FILE).exists():primary.append(net/MODULE_FILE)
    provenance=dict(version=VERSION,inputs={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in primary},
        candidates=int(candidates.sequence_id.nunique()),families=len(inventory),species=species,
        grade_counts={g:int(candidates.grade.eq(g).sum()) for g in ['A','B','C','D']},**diagnostics)
    outputs={EDGE_FILE:edges,INVENTORY_FILE:inventory,MEMBERS_FILE:members}
    storage_error=''
    if persist:
        try:
            for name,frame in outputs.items():_write_changed(net/name,frame.to_csv(index=False,lineterminator='\n'))
            _write_changed(root/'.atlas_cache/library_refresh.json',json.dumps(provenance,ensure_ascii=False,sort_keys=True,indent=2))
        except OSError as error:storage_error=str(error)
    return dict(reference=edges.copy(deep=True),inventory=inventory,members=members,provenance=provenance,storage_error=storage_error)


def _data_span(html):
    match=re.search(r'\bconst\s+DATA\s*=\s*',html)
    if not match:raise ValueError('Interactive family HTML needs its DATA model to refresh the network.')
    model,end=json.JSONDecoder().raw_decode(html[match.end():])
    return match.end(),match.end()+end,model


def refresh_family_html(html,candidates,root):
    """Refresh only data/grade adapters; keep authored controls, special evidence and styling."""
    start,end,old=_data_span(html);snapshot=refresh_derived(candidates,root,persist=False)
    inventory=snapshot['inventory'];reference=snapshot['reference'];active=set(candidates.family)
    families=[]
    for row in inventory.to_dict('records'):
        group=candidates[candidates.family.eq(row['family'])]
        families.append(dict(id=row['family'],zone=row['visual_group'],n=int(row['total']),
            counts={s:int(group.species.eq(s).sum()) for s in sorted(candidates.species.unique())},
            grade_by_species={s:{g:int((sub.grade==g).sum()) for g in ['A','B','C','D']} for s,sub in group.groupby('species')},
            grades={g:int(group.grade.eq(g).sum()) for g in ['A','B','C','D']},strong=int(group.grade.isin(['A','B']).sum()),
            human_symbols=[s for s in row['human_mapping_symbols'].split(';') if s]))
    field_map={'s':'species','id':'sequence_id','f':'family','c':'assignment_confidence','g':'grade','support':'family_support_level',
        'decision':'family_decision','name':'candidate_annotation','pfam':'architecture','cdd':'NCBI_CDD_architecture',
        'hog':'orthogroup','orthostat':'orthology_scope','local':'DeepLoc_2.1','motif':'MotifPrediction_distinct_site_count'}
    frame=candidates.reindex(columns=list(field_map.values())).rename(columns={v:k for k,v in field_map.items()})
    records=json.loads(frame.to_json(orient='records'));edges=[]
    for row in reference.to_dict('records'):
        if row['family_A'] not in active or row['family_B'] not in active:continue
        pairs=row['human_symbol_pairs'].split('; ')
        edges.append(dict(id=row['family_A']+'::'+row['family_B'],a=row['family_A'],b=row['family_B'],kind='human_reference_transfer',
            raw=int(row['original_rows']),human_pairs=int(row['human_reference_pairs']),example_pairs=pairs[:8],pairlist=pairs,
            pmids=[s for s in row['PMIDs'].split('; ') if s],sources=[s for s in row['data_sources'].split('; ') if s],
            types=json.loads(row['interaction_types']),effects=json.loads(row['effects'])))
    by_id=candidates.set_index('sequence_id').family.to_dict();special=[]
    for edge in old.get('special',[]):
        named=[by_id.get(identifier) for identifier in edge.get('ids',[])]
        if named and all(identifier in by_id for identifier in edge['ids']) and edge['a'] in named and (edge['b']=='SmVKR1' or edge['b'] in named):special.append(edge)
    zones=list(dict.fromkeys([z for z in old.get('zones',[]) if z in set(inventory.visual_group)]+list(inventory.visual_group)))
    model={**old,'meta':{**old.get('meta',{}),**snapshot['provenance'],'proteins':len(candidates),'families':len(families),
        'human_original_rows':snapshot['provenance']['reference_rows'],'human_mapped_rows':snapshot['provenance']['mapped_rows'],
        'human_interfamily_edges':len(edges),'human_intrfamily_groups':snapshot['provenance']['intrafamily_groups'],
        'human_distinct_symbols':snapshot['provenance']['distinct_reference_symbols'],
        'human_matched_symbols':snapshot['provenance']['matched_symbols'],'source_files':list(snapshot['provenance']['inputs']),
        'candidate_sha256':snapshot['provenance']['inputs']['files/adhesome_candidates_list.xlsx'],
        'interactions_sha256':snapshot['provenance']['inputs']['adhesome_network/interactions.csv']},
        'families':families,'candidates':records,'edges':edges,'special':special,'zones':zones,
        'core':[f for f in old.get('core',[]) if f in active]}
    html=html[:start]+json.dumps(model,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+html[end:]
    return _dynamic_family_controls(html)


def _dynamic_family_controls(html):
    html=re.sub(r'const ZONECOLORS=\[[^\]]*\];',"const ZONECOLORS=['#16724e','#166b84','#956415','#8a4050','#6650a7','#526b86','#64746d','#536c80','#79664f'];",html,count=1)
    html=html.replace("['All seven species',...DATA.meta.species]","['All '+DATA.meta.species.length+' species',...DATA.meta.species]")
    html=html.replace('extent={w:1568,h:Math.max','extent={w:8+zones.length*260,h:Math.max')
    html=re.sub(r'function chooseRows\(f,opts\)\{.*?(?=function countFmt)',
        "function chooseRows(f,opts){let a=proteinsByFamily[f]||[];if(opts.species!=='all')a=a.filter(r=>r.s===opts.species);if(opts.grade!=='all')a=a.filter(r=>opts.grade==='AB'?['A','B'].includes(r.g):r.g===opts.grade);return a}\n",html,count=1,flags=re.S)
    html=re.sub(r'function summaryStats\(opts\)\{.*?(?=function selectedEvidenceFilter)',r'''function summaryStats(opts){const all=DATA.candidates.filter(p=>(opts.species==='all'||p.s===opts.species)&&(opts.grade==='all'||opts.grade==='AB'&&['A','B'].includes(p.g)||p.g===opts.grade));
const counts=['A','B','C','D'].map(g=>all.filter(p=>p.g===g).length).join(' / '),fields=[['Candidates',all.length,'protein records'],['Inventory groups',visibleFamilies.length,'displayed in network'],['Human ref. edges',activeEdges.filter(e=>e.kind==='human_reference_transfer').length,'family-level hypotheses'],['Grades A / B / C / D',counts,'D = unassigned']];
$('topstats').innerHTML=fields.map(([n,v,tag])=>`<div class="metric"><span>${escapeHtml(n)}</span><b>${escapeHtml(v)}</b><small>${escapeHtml(tag)}</small></div>`).join('')}
''',html,count=1,flags=re.S)
    html=html.replace('gradeC=r.length-gradeA-gradeB','gradeC=r.filter(x=>x.g===\'C\').length,gradeD=r.filter(x=>x.g===\'D\').length')
    html=html.replace(' B ${gradeB}  C ${gradeC}`', ' B ${gradeB}  C ${gradeC}  D ${gradeD}`')
    html=html.replace('Current seven-species candidate inventory','Current '+"${DATA.meta.species.length}"+'-species candidate inventory')
    html=html.replace('provisional-family records. These grades','provisional-family records; <b>D = ${countFmt(DATA.meta.grade_counts.D||0)}</b> unassigned records. These grades')
    for name in ['C','D']:
        pattern=r'(<select\b[^>]*\bid=[\"\']grade[\"\'][^>]*>)(.*?)(</select>)'
        def add_option(match):
            if re.search(r'value=[\"\']'+name+r'[\"\']',match[2]):return match[0]
            return match[1]+match[2]+f'<option value="{name}">{name} · '+('Provisional' if name=='C' else 'Unassigned')+'</option>'+match[3]
        html=re.sub(pattern,add_option,html,count=1,flags=re.S)
    # Default to the complete inventory; the authored core subset remains available.
    def all_scope(match):
        options=re.sub(r'\sselected(?:=[\"\'][^\"\']*[\"\'])?','',match[2])
        options=re.sub(r'(<option\b[^>]*value=[\"\']all[\"\'])',r'\1 selected',options,count=1)
        return match[1]+options+match[3]
    html=re.sub(r'(<select\b[^>]*\bid=[\"\']scope[\"\'][^>]*>)(.*?)(</select>)',all_scope,html,count=1,flags=re.S)
    return html
