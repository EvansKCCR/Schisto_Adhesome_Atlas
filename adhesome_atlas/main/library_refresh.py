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

VERSION='library-refresh-6'
EDGE_FILE='Schistosome_human_reference_family_edges.csv'
INVENTORY_FILE='Schistosome_adhesome_family_inventory.csv'
MEMBERS_FILE='Schistosome_adhesome_candidate_node_members.csv'
MODULE_FILE='family_module_annotations.csv'
DERIVED_FILES={EDGE_FILE,INVENTORY_FILE,MEMBERS_FILE}
UNRESOLVED='Unassigned/unresolved'
EDGE_COLUMNS=['family_A','family_B','human_reference_pairs','original_rows','human_symbol_pairs',
    'interaction_types','effects','PMIDs','data_sources','evidence_interpretation']


def family_key(value):
    """Join audited names to the corresponding historical crosswalk labels."""
    if pd.isna(value): return ''
    key=re.sub(r'[\W_]+',' ',str(value).casefold()).strip()
    return {
        'talin like':'talin',
        'filamin like':'filamin',
        'adam like metalloprotease':'adam like',
    }.get(key,key)


def family_index(labels):
    result=defaultdict(list)
    for label in sorted(set(labels)):
        key=family_key(label)
        if key: result[key].append(label)
    return result


def align_family_annotations(annotations,families):
    """Join unambiguous formatting variants without guessing biological synonyms."""
    grouped=defaultdict(set)
    for family,value in annotations.items():grouped[family_key(family)].add(value)
    return {family:next(iter(grouped[family_key(family)])) for family in families
        if len(grouped[family_key(family)])==1}


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


def module_annotations(root,families=None):
    from functional_categories import reference_mapping
    net=Path(root)/'adhesome_network';path=net/MODULE_FILE
    # Backwards-compatible first launch; the separate editable mapping avoids a
    # circular dependency between regenerated inventory counts and module annotations.
    if not path.exists():path=net/INVENTORY_FILE
    if not path.exists():return {}
    annotations=pd.read_csv(path,dtype=str).fillna('')
    _required(annotations,['family','visual_group'],path.name)
    if annotations.family.duplicated().any():raise ValueError('Module annotations contain duplicate family keys.')
    result=dict(zip(annotations.family,annotations.visual_group))
    # Function-first reference takes precedence over historical display categories.
    reference=reference_mapping(root)
    result={family:reference.get(family_key(family),module) for family,module in result.items()}
    if families is not None:
        for family in families:
            if family_key(family) in reference:result[family]=reference[family_key(family)]
    return result if families is None else align_family_annotations(result,families)


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
    from functional_categories import support_state,SUMMARY_FILE
    root=Path(root);net=root/'adhesome_network'
    raw_bytes=(net/'interactions.csv').read_bytes();cross_bytes=(net/'Schistosome_human_gene_family_crosswalk.csv').read_bytes()
    edges,diagnostics=_cached_reference(raw_bytes,cross_bytes)
    crosswalk=_csv(cross_bytes);groups=module_annotations(root,candidates.family);species=sorted(candidates.species.unique());inventory=[]
    symbol_map=crosswalk.assign(family_key=crosswalk.candidate_family.map(family_key)).groupby('family_key').human_symbol.agg(lambda s:';'.join(sorted(set(s)))).to_dict()
    counts=candidates[['family','sequence_id','species','grade']].assign(support=support_state(candidates))
    for family,group in counts.groupby('family',sort=True):
        supported=group.support.isin(['specific supported','broad supported'])
        row=dict(family=family,visual_group=(groups.get(family) or UNRESOLVED) if supported.any() else UNRESOLVED,
            assignment_records=len(group),total=group.sequence_id.nunique(),
            supported_proteins=group.loc[supported,'sequence_id'].nunique(),
            unsupported_proteins=group.loc[~supported,'sequence_id'].nunique(),
            **{'grade_'+grade:group.loc[group.grade.eq(grade),'sequence_id'].nunique() for grade in ['A','B','C','D']},
            human_mapping_symbols=symbol_map.get(family_key(family),''))
        row.update({name:group.loc[group.species.eq(name),'sequence_id'].nunique() for name in species});inventory.append(row)
        row.update({'support_'+state.replace(' ','_'):int(count)
                    for state,count in group.drop_duplicates('sequence_id').support.value_counts().items()})
    inventory=pd.DataFrame(inventory)
    members=candidates[['species','sequence_id','family','grade','assignment_confidence','family_decision','architecture']].rename(
        columns={'sequence_id':'protein_id','family':'putative_audited_family','architecture':'Pfam_architecture'})
    for field in ['protein_name','orthogroup','family_support_level','annotation_resolution',
                  'annotation_notes','NCBI_CDD_architecture','DeepLoc_2.1','DeepTMHMM','SignalP.v6.0','module']:
        if field in candidates:members[field]=candidates[field].values
    primary=[root/'files/adhesome_candidates_list.xlsx',net/'interactions.csv',net/'Schistosome_human_gene_family_crosswalk.csv']
    if (net/MODULE_FILE).exists():primary.append(net/MODULE_FILE)
    if (root/SUMMARY_FILE).exists():primary.append(root/SUMMARY_FILE)
    if (root/'notes/Target_prioritization.md').exists():primary.append(root/'notes/Target_prioritization.md')
    provenance=dict(version=VERSION,inputs={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in primary},
        assignment_records=len(candidates),candidates=int(candidates.sequence_id.nunique()),families=len(inventory),species=species,
        grade_counts={g:int(candidates.grade.eq(g).sum()) for g in ['A','B','C','D']},
        unique_grade_counts={g:int(candidates.loc[candidates.grade.eq(g),'sequence_id'].nunique()) for g in ['A','B','C','D']},
        support_counts={str(state):int(n) for state,n in support_state(candidates.drop_duplicates('sequence_id')).value_counts().items()},
        **diagnostics)
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


def refresh_family_html(html,candidates,root,literature=None):
    """Refresh only data/grade adapters; keep authored controls, special evidence and styling."""
    from functional_categories import CATEGORIES,support_state
    start,end,old=_data_span(html);snapshot=refresh_derived(candidates,root,persist=False)
    inventory=snapshot['inventory'];reference=snapshot['reference'];active=set(candidates.family)
    aliases=family_index(active)
    families=[]
    memberships=candidates[['family','sequence_id','species','grade']].assign(support=support_state(candidates))
    grouped=dict(tuple(memberships.drop_duplicates(['family','sequence_id']).groupby('family',sort=False)))
    species_names=sorted(memberships.species.unique())
    for row in inventory.to_dict('records'):
        group=grouped[row['family']]
        families.append(dict(id=row['family'],zone=row['visual_group'],n=int(row['total']),
            supported_n=int(row['supported_proteins']),unsupported_n=int(row['unsupported_proteins']),
            support_counts={str(state):int(n) for state,n in group.support.value_counts().items()},
            counts={s:int(group.species.eq(s).sum()) for s in species_names},
            grade_by_species={s:{g:int((sub.grade==g).sum()) for g in ['A','B','C','D']} for s,sub in group.groupby('species')},
            grades={g:int(group.grade.eq(g).sum()) for g in ['A','B','C','D']},strong=int(row['supported_proteins']),
            human_symbols=[s for s in row['human_mapping_symbols'].split(';') if s]))
    field_map={'s':'species','id':'sequence_id','f':'family','c':'assignment_confidence','g':'grade','support':'family_support_level',
        'decision':'family_decision','name':'candidate_annotation','pfam':'architecture','cdd':'NCBI_CDD_architecture',
        'hog':'orthogroup','orthostat':'orthology_scope','local':'DeepLoc_2.1','module':'module',
        'motif':'MotifPrediction_distinct_site_count'}
    frame=candidates.reindex(columns=list(field_map.values())).rename(columns={v:k for k,v in field_map.items()})
    records=json.loads(frame.to_json(orient='records'));edges=[]
    supported_members=memberships.loc[memberships.support.isin(['specific supported','broad supported']),
                                       ['family','sequence_id','species']]
    supported_by_family=dict(tuple(supported_members.groupby('family')))
    for row in reference.to_dict('records'):
        pairs=row['human_symbol_pairs'].split('; ')
        for left,right in product(aliases.get(family_key(row['family_A']),[]),aliases.get(family_key(row['family_B']),[])):
            if family_key(left)==family_key(right):continue
            if left not in supported_by_family or right not in supported_by_family:continue
            source=supported_by_family[left];target=supported_by_family[right]
            shared=sorted(set(source.species)&set(target.species))
            if not shared:continue
            edges.append(dict(id=left+'::'+right,a=left,b=right,kind='human_reference_transfer',
                shared_species=shared,source_candidates=sorted(set(source.loc[source.species.isin(shared),'sequence_id'])),
                target_candidates=sorted(set(target.loc[target.species.isin(shared),'sequence_id'])),
                reference_family_A=row['family_A'],reference_family_B=row['family_B'],
                raw=int(row['original_rows']),human_pairs=int(row['human_reference_pairs']),example_pairs=pairs[:8],pairlist=pairs,
                pmids=[s for s in row['PMIDs'].split('; ') if s],sources=[s for s in row['data_sources'].split('; ') if s],
                types=json.loads(row['interaction_types']),effects=json.loads(row['effects'])))
    by_id=candidates.set_index('sequence_id').family.to_dict();special=[]
    for edge in old.get('special',[]):
        lefts=aliases.get(family_key(edge['a']),[])
        rights=['SmVKR1'] if edge['b']=='SmVKR1' else aliases.get(family_key(edge['b']),[])
        # Literature context is anchored to published named proteins. Only the
        # registry can identify a matching modern accession as directly studied.
        for left,right in product(lefts,rights):
            context={**edge,'a':left,'b':right,'ids':[pid for pid in edge.get('ids',[]) if pid in by_id]}
            if literature:
                from literature import named_reference_ids
                context['reference_ids']=['R02']
                context['interaction_id']=edge['id']
                context['evidence_origin']='schistosoma_pathway'
                context['direct_candidate_ids']=sorted(set(context['ids'])&named_reference_ids(literature,'R02'))
            special.append(context)
    zones=[z for z in CATEGORIES if z in set(inventory.visual_group)]
    zones+=sorted(set(inventory.visual_group)-set(zones))
    old_metadata={key:value for key,value in old.get('meta',{}).items() if key!='reclassification'}
    model={**old,'meta':{**old_metadata,**snapshot['provenance'],'proteins':len(candidates),'families':len(families),
        'human_original_rows':snapshot['provenance']['reference_rows'],'human_mapped_rows':snapshot['provenance']['mapped_rows'],
        'human_interfamily_edges':len(edges),'human_intrfamily_groups':snapshot['provenance']['intrafamily_groups'],
        'human_distinct_symbols':snapshot['provenance']['distinct_reference_symbols'],
        'human_matched_symbols':snapshot['provenance']['matched_symbols'],'source_files':list(snapshot['provenance']['inputs']),
        'candidate_sha256':snapshot['provenance']['inputs']['files/adhesome_candidates_list.xlsx'],
        'interactions_sha256':snapshot['provenance']['inputs']['adhesome_network/interactions.csv']},
        'families':families,'candidates':records,'edges':edges,'special':special,'zones':zones,
        'core':sorted({label for family in old.get('core',[]) for label in aliases.get(family_key(family),[])}|
            set(inventory.loc[inventory.visual_group.eq('Membrane-actin clutch')&inventory.supported_proteins.gt(0),'family']))}
    if literature:
        from literature import references_for_pmids, projected_interaction_id
        for edge in edges:
            edge['reference_ids']=references_for_pmids(literature,edge['pmids'])
            edge['interaction_id']=projected_interaction_id(edge['reference_family_A'],edge['reference_family_B'])
            edge['evidence_origin']='reference_projected_interaction'
    html=html[:start]+json.dumps(model,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+html[end:]
    return _dynamic_family_controls(html)


def _dynamic_family_controls(html):
    html=html.replace('All A / B / C</option>','All A / B / C / D</option>')
    html=re.sub(r'const ZONECOLORS=\[[^\]]*\];',"const ZONECOLORS=['#16724e','#166b84','#956415','#8a4050','#6650a7','#526b86','#64746d','#536c80','#79664f'];",html,count=1)
    html=html.replace("['All seven species',...DATA.meta.species]","['All '+DATA.meta.species.length+' species',...DATA.meta.species]")
    html=html.replace('B · Unassigned','Grade B').replace('C · Provisional','Grade C').replace('D · Unassigned','Grade D')
    html=html.replace('Solid-border nodes: ≥1 grade A/B assignment · dashed: grade C only',
        'Solid-border nodes have a specific or broad supported candidate in view')
    html=html.replace("gradeA+gradeB?'':'5 4'","r.some(x=>['specific supported','broad supported'].includes(x.support))?'':'5 4'")
    html=html.replace('Receptor context from the previously supplied model and Gelmedin et al. (2017).',
                      'Receptor context from the Gelmedin et al. (2017) study.')
    html=html.replace('extent={w:1568,h:Math.max','extent={w:8+zones.length*260,h:Math.max')
    html=re.sub(r'function chooseRows\(f,opts\)\{.*?(?=function countFmt)',
        "function chooseRows(f,opts){const seen=new Set();let a=(proteinsByFamily[f]||[]).filter(r=>{if(seen.has(r.id))return false;seen.add(r.id);return true});if(opts.species!=='all')a=a.filter(r=>r.s===opts.species);if(opts.grade!=='all')a=a.filter(r=>opts.grade==='AB'?['A','B'].includes(r.g):r.g===opts.grade);return a}\n",html,count=1,flags=re.S)
    html=re.sub(r'function summaryStats\(opts\)\{.*?(?=function selectedEvidenceFilter)',r'''function summaryStats(opts){const all=DATA.candidates.filter(p=>(opts.species==='all'||p.s===opts.species)&&(opts.grade==='all'||opts.grade==='AB'&&['A','B'].includes(p.g)||p.g===opts.grade));
const counts=['A','B','C','D'].map(g=>all.filter(p=>p.g===g).length).join(' / '),fields=[['Candidates',all.length,'protein records'],['Inventory groups',visibleFamilies.length,'displayed in network'],['Human ref. edges',activeEdges.filter(e=>e.kind==='human_reference_transfer').length,'family-level hypotheses'],['Grades A / B / C / D',counts,'source grades']];
$('topstats').innerHTML=fields.map(([n,v,tag])=>`<div class="metric"><span>${escapeHtml(n)}</span><b>${escapeHtml(v)}</b><small>${escapeHtml(tag)}</small></div>`).join('')}
''',html,count=1,flags=re.S)
    html=html.replace('gradeC=r.length-gradeA-gradeB','gradeC=r.filter(x=>x.g===\'C\').length,gradeD=r.filter(x=>x.g===\'D\').length')
    html=html.replace(' B ${gradeB}  C ${gradeC}`', ' B ${gradeB}  C ${gradeC}  D ${gradeD}`')
    html=html.replace('Current seven-species candidate inventory','Current '+"${DATA.meta.species.length}"+'-species candidate inventory')
    html=re.sub(r'<h3>Current audit grades</h3><p>.*?</p>',
        lambda _:'''<h3>Audited support categories</h3><p>${Object.entries(DATA.meta.support_counts||{}).map(([state,n])=>escapeHtml(state)+' '+countFmt(n)).join(' · ')}. Source grades are listed separately above the map.</p>''',html,count=1,flags=re.S)
    html=html.replace("if(o.human)activeEdges.push(...DATA.edges.filter(e=>included.has(e.a)&&included.has(e.b)&&e.human_pairs>=o.minPairs));",
        """if(o.human){
 const eligible=new Map(DATA.candidates.filter(p=>(o.species==='all'||p.s===o.species)
  &&(o.grade==='all'||o.grade==='AB'&&['A','B'].includes(p.g)||o.grade===p.g)).map(p=>[p.id,p.s]));
 activeEdges.push(...DATA.edges.filter(e=>included.has(e.a)&&included.has(e.b)&&e.human_pairs>=o.minPairs
  &&e.shared_species.some(species=>e.source_candidates.some(id=>eligible.get(id)===species)
   &&e.target_candidates.some(id=>eligible.get(id)===species))));
}""")
    for name in ['B','C','D']:
        pattern=r'(<select\b[^>]*\bid=[\"\']grade[\"\'][^>]*>)(.*?)(</select>)'
        def add_option(match):
            if re.search(r'value=[\"\']'+name+r'[\"\']',match[2]):return match[0]
            return match[1]+match[2]+f'<option value="{name}">Grade {name}</option>'+match[3]
        html=re.sub(pattern,add_option,html,count=1,flags=re.S)
    # Default to the complete inventory; the authored core subset remains available.
    def all_scope(match):
        options=re.sub(r'\sselected(?:=[\"\'][^\"\']*[\"\'])?','',match[2])
        options=re.sub(r'(<option\b[^>]*value=[\"\']all[\"\'])',r'\1 selected',options,count=1)
        return match[1]+options+match[3]
    html=re.sub(r'(<select\b[^>]*\bid=[\"\']scope[\"\'][^>]*>)(.*?)(</select>)',all_scope,html,count=1,flags=re.S)
    return html
