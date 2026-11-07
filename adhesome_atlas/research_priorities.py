"""Source-driven research entry point; never changes candidate scores or assignments."""
from html import escape
from pathlib import Path
import re
from urllib.parse import urlencode, urlsplit, urlunsplit

from candidate_profiles import atlas_url


OVERVIEW = ('The Schisto-Adhesome Atlas provides a comparative framework for identifying and '
    'prioritizing adhesion-associated proteins across medically important Schistosoma species. '
    'Candidate prioritization integrates protein-family evidence, orthology, predicted biological '
    'function, host similarity, and published experimental findings to identify promising targets '
    'for further investigation.')

# Presentation metadata and explicit family joins; all counts, IDs, rationale and references
# are read from Target_prioritization.md on each page run.
FEATURES = [
    dict(key='tetraspanins', families=('tetraspanin_like',), label='Tetraspanin-like proteins',
         objective='Comparative vaccine-antigen discovery',
         next='Extracellular-loop architecture, EC2 conservation, and tegument accessibility.'),
    dict(key='calpains', families=('calpain_like',), label='Calpain-like cysteine proteases',
         objective='Vaccine-antigen evaluation and comparative protease characterization',
         next='Expression conservation, biochemical characterization, and host–parasite selectivity.'),
    dict(key='integrins', families=('integrin_alpha', 'integrin_beta'), label='Integrin α/β receptors',
         objective='Receptor function, reproduction, and adhesion signaling',
         next='Receptor pairing, domain architecture, ligand recognition, and functional validation.'),
]
FAMILY_JOINS = {
    'Src-family kinases': ('Src',), 'FAK': ('FAK',), 'ILK': ('ILK',),
    'Kindlin': ('kindlin',), 'Talin': ('talin',), 'Vinculin': ('vinculin',),
    'Collagen-/laminin-like': ('collagen_like', 'laminin_like'),
    'PINCH-like adaptors':('PINCH_like',),'Parvin-like actin adaptors':('Parvin_like',),
    'Paxillin-like adaptors':('paxillin_like',),'Nck adaptors':('Nck',),
    'PAK-like kinases':('PAK_like',),'Rho GTPase-like proteins':('Rho_GTPase_like',),
    'PKC-like kinases':('PKC_like',),'Alpha-actinin and filamin':('alpha_actinin','filamin'),
    'ARPC2-like actin nucleation components':('ARPC2_like',),'PIP5K-like lipid kinases':('PIP5K_like',),
    'ADAM-like membrane metalloproteases':('ADAM_like',),'KCNH-like potassium channels':('KCNH_like',),
    'MAPK-like kinases':('MAPK-like',),
    'Fatty-acid-binding proteins':('Fatty-acid-binding protein (FABP)-like',),
}
# Explicit display joins for the two catalogue naming versions. No source family
# assignments are renamed, inferred or combined with a different biological family.
FAMILY_ALIASES = {
    'tetraspanin_like': ('tetraspanin_like','tetraspanin-like'),
    'calpain_like': ('calpain_like','calpain-like'),
    'integrin_alpha': ('integrin_alpha','integrin alpha'),
    'integrin_beta': ('integrin_beta','integrin beta'),
    'collagen_like': ('collagen_like','collagen-like'),
    'laminin_like': ('laminin_like','laminin-like'),
}
CHALLENGES = {
    'Src-family kinases': 'Establish host-kinase selectivity.',
    'FAK': 'Resolve ambiguous FAK-like assignments and adhesion-associated signaling.',
    'ILK': 'Establish scaffold function; do not assume conventional kinase activity.',
    'Kindlin': 'Test receptor activation and integrin-associated complex formation.',
    'Talin': 'Test cytoskeletal coupling and selective small-molecule tractability.',
    'Vinculin': 'Test assembly of the predicted adhesion machinery.',
    'Collagen-/laminin-like': 'Validate family identity, host similarity and extracellular ligand or antigen function.',
}


TABLE_HEADERS={
    'Candidate or orthogroup':('Candidate or orthogroup','Development objective','First decisive experiment or analysis'),
    'Protein ID':('Protein ID','Assignment','Main justification'),
    'Candidate family':('Candidate family','Supported proteins','Representative S. mansoni IDs','Priority and rationale'),
    'Evaluation criterion':('Evaluation criterion','Vaccine/antibody candidate','Small-molecule drug candidate'),
}
CITATION_PATTERN=r'\[([^\]\n]+)\]\((https://(?:doi\.org|pubmed\.ncbi\.nlm\.nih\.gov)/[^\s)]+)\)|\(([^()\n]+)\)\[(https://(?:doi\.org|pubmed\.ncbi\.nlm\.nih\.gov)/[^\]\s]+)\]'


def _plain_cells(line,first_header):
    """Recognize explicit ID/classification and prose boundaries in plain-text tables.

    Ambiguous rows fail rather than silently shifting scientific content between
    columns. Tabs and Markdown pipes support arbitrary prose without these rules.
    """
    patterns={
        'Candidate or orthogroup':r'^((?:OG\d+(?:/OG\d+)*\s+\S+)|(?:.+?\([^)]*(?:Smp_|OG)\d+[^)]*\))|(?:.+?\brepresentatives))\s+(.+?\b(?:discovery|target|mechanism|characterization|validation|investigation|evaluation))\s+(.+)$',
        'Protein ID':r'^(\S+)\s+((?:Supported|Provisional|Unassigned|Unresolved)\s+integrin\s+(?:alpha|beta|α|β)(?:\s+hypothesis)?)\s+(.+)$',
        'Candidate family':r'^(.+?)\s+(\d+.*?)\s+(Smp_\d+(?:\s*,\s*Smp_\d+)*)\s+(.+)$',
    }
    if first_header=='Evaluation criterion':
        starts=list(re.finditer(r'(?<!\S)[A-Z][a-z]{2,}[\w/-]*',line))
        if len(starts)==3 and starts[0].start()==0:
            return [line[starts[i].start():starts[i+1].start()].strip() for i in range(2)]+[line[starts[2].start():]]
    else:
        match=re.fullmatch(patterns[first_header],line,re.I)
        if match:return list(match.groups())
    raise ValueError('Ambiguous '+first_header+' table row; use tabs or Markdown pipes: '+line)


def _table_block(text, first_header):
    """Read tab, Markdown-pipe and recognizable space-separated source tables."""
    lines=text.splitlines();headers=TABLE_HEADERS[first_header]
    normalized=lambda value:' '.join(value.replace('|',' ').split())
    start=next((i for i,line in enumerate(lines) if normalized(line)==normalized(' '.join(headers))),None)
    if start is None:raise ValueError('Missing research-priority table: '+first_header)
    rows=[];end=start+1
    for index in range(start+1,len(lines)):
        line=lines[index].strip()
        if not line:break
        end=index+1
        if re.fullmatch(r'[|:\-\s]+',line):continue
        if '\t' in line:values=[v.strip() for v in line.split('\t')]
        elif line.startswith('|') and line.endswith('|'):values=[v.strip() for v in line[1:-1].split('|')]
        else:
            values=re.split(r'\s{2,}',line)
            if len(values)!=len(headers):values=_plain_cells(' '.join(line.split()),first_header)
        if len(values)!=len(headers) or any(not value for value in values):
            raise ValueError('Incomplete research-priority table row: '+line)
        rows.append(dict(zip(headers,values)))
    if not rows:raise ValueError('Empty research-priority table: '+first_header)
    return rows,start,end


def _tabular(text,first_header):
    return _table_block(text,first_header)[0]


def _number(value):
    if value.isdigit():return int(value)
    words='zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split()
    if value.lower() not in words:raise ValueError('Unrecognized count in the research brief: '+value)
    return words.index(value.lower())


def load_brief(path):
    text=Path(path).read_text(encoding='utf-8-sig')
    sections=re.split(r'^##\s+\*\*Target\s+\d+[^\n]*\n',text,flags=re.M)
    prefix=sections[0];chunks=sections[1:]
    if len(chunks)!=3:raise ValueError('Expected three featured Target headings in Target_prioritization.md.')
    # The third section ends where the additional-family table begins.
    chunks[-1]=re.split(r'^(?:\d+[.)]\s+|#{1,6}\s*)\**Additional candidates\b',chunks[-1],flags=re.M|re.I)[0]
    features=[]
    for spec,chunk in zip(FEATURES,chunks):
        count_line=next(line[2:] for line in chunk.splitlines() if line.startswith('- ') and 'supported' in line)
        if spec['key']=='integrins':
            clauses=re.findall(r'(\w+)\s+(supported|provisional|unassigned|unresolved)\s+integrin\s+(alpha|beta|α|β)',count_line,re.I)
            if not clauses:raise ValueError('Cannot read integrin α/β classifications in the priority brief.')
            metrics=[]
            for count,status,subunit in clauses:
                status='Unassigned' if status.lower() in {'unassigned','unresolved'} else status.capitalize()
                subunit='α' if subunit.lower() in {'α','alpha'} else 'β'
                metric=dict(label=f'Integrin {subunit}'+(' hypothesis' if status=='Unassigned' else '')+' · '+status.lower(),
                    count=_number(count),families=('integrin_alpha' if subunit=='α' else 'integrin_beta',),classification=status)
                if status=='Unassigned':metric['hypothesis_field']='stage1_family_hypothesis'
                metrics.append(metric)
            assignments,table_start,table_end=_table_block(chunk,'Protein ID')
        else:
            found=re.search(r'(\d+) supported candidates across (\w+) orthogroups',count_line)
            if not found:raise ValueError('Cannot read candidate/orthogroup counts in the priority brief.')
            group_count=_number(found[2])
            metrics=[dict(label='Supported candidates',count=int(found[1]),families=spec['families'],classification='Supported'),
                     dict(label='Supported orthogroups',count=group_count,families=spec['families'],classification='Supported',orthogroups=True)]
            assignments=[];table_start=table_end=-1
        # Retain the scientific prose and every reference, including the named calpain bullets.
        evidence=[]
        for index,line in enumerate(chunk.splitlines()):
            if table_start<=index<table_end or not line.strip() or line.removeprefix('- ')==count_line or line.startswith('- Key orthogroups:') or line.startswith('- Representative') or re.match(r'- (?:Two|Three) S\. mansoni',line):continue
            evidence.append(line.removeprefix('- '))
        features.append({**spec,'metrics':metrics,'count_text':count_line,
            'orthogroups':list(dict.fromkeys(re.findall(r'OG\d{7}',chunk))),
            'proteins':list(dict.fromkeys(re.findall(r'Smp_\d+',chunk))),
            'evidence':evidence,'assignments':assignments})
    additional=_tabular(text,'Candidate family')
    for row in additional:
        row['families']=FAMILY_JOINS.get(row['Candidate family'],())
        row['count']=int(re.search(r'\d+',row['Supported proteins'])[0])
        row['orthogroups']=tuple(dict.fromkeys(re.findall(r'OG\d{7}',row['Priority and rationale']))) if not row['families'] else ()
        row['challenge']=CHALLENGES.get(row['Candidate family'],row['Priority and rationale'])
    references=[]
    for match in re.finditer(CITATION_PATTERN,text):
        label,url=(match[1],match[2]) if match[1] else (match[3],match[4])
        if url not in [r['url'] for r in references]:references.append(dict(label=label,url=url))
    roadmap_rows=_tabular(text,'Candidate or orthogroup');roadmap=[];seen=set()
    for row in roadmap_rows:
        identity=tuple(' '.join(value.split()) for value in row.values())
        if identity not in seen:roadmap.append(row);seen.add(identity)
    intro=prefix.split('Candidate or orthogroup')[0]
    overview=' '.join(line.strip() for line in intro.splitlines() if line.strip().strip('|') and not line.startswith('#') and not re.match(r'\d+[.)]\s',line))
    _,_,additional_end=_table_block(text,'Candidate family')
    tail='\n'.join(text.splitlines()[additional_end:])
    additional_evidence=re.split(r'^\s*3[.)]\s+\**A practical target-selection framework',tail,flags=re.M|re.I)[0].strip()
    _,_,framework_end=_table_block(text,'Evaluation criterion')
    framework_text='\n'.join(text.splitlines()[framework_end:]).strip()
    return dict(features=features,additional=additional,framework=_tabular(text,'Evaluation criterion'),
                roadmap=roadmap,references=references,overview=overview or OVERVIEW,
                additional_evidence=additional_evidence,framework_text=framework_text,
                repeated_roadmap_rows=len(roadmap_rows)-len(roadmap))


def protein_matches(candidates,identifier):
    """Exact full IDs or exact accession suffixes only; never a substring family guess."""
    return candidates[candidates.sequence_id.eq(identifier) | candidates.sequence_id.str.split('__').str[-1].eq(identifier)]


def target_url(base,view,**selection):
    if view=='Protein dossier':return atlas_url(base,view,selection['protein'])
    parts=urlsplit(base or '')
    return urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode({'view':view,**selection}),''))


def apply_target_route(candidates,params,state):
    """Apply a deep link once, before creating sidebar or destination widgets."""
    view,protein,family,group=(params.get(k,'') for k in ('view','protein','family','orthogroup'))
    from navigation import HYPOTHESIS_PAGE,PAGES
    if view=='Introduction' and (protein or params.get('classification')=='pfam_cdd'):view=HYPOTHESIS_PAGE
    route=(view,protein,family,group,params.get('workspace',''),params.get('classification',''))
    if state.get('atlas_route')==route:return
    state['atlas_route']=route
    if view in PAGES:state['atlas_page']=view
    if protein in set(candidates.sequence_id):
        state['map_candidate']=protein;state['dossier_protein']=protein
    if view=='Components' and family in set(candidates.family):
        state['catalogue_families']=[family]
        state['catalogue_species']=sorted(candidates.species.unique())
        state['catalogue_classification']='All';state['catalogue_query']=''
        state['component_section']='Candidate catalogue'
    if view=='Orthology' and group:
        state['orthology_query']=group
        state['orthology_families']=[]
        state['orthology_route_group']=group
    if view=='Phylogeny' and group:state['phylogeny_route_group']=group


def _link(label,url,kind='target',title=''):
    return (f'<a class="research-link research-{kind}" href="{escape(url,quote=True)}" '
        f'target="_self" title="{escape(title or label,quote=True)}">{escape(label)}</a>')


def protein_links(identifier,candidates,base):
    matches=protein_matches(candidates,identifier).drop_duplicates('sequence_id')
    if matches.empty:return f'<span class="research-unavailable" title="No matching candidate in the current catalogue">{escape(identifier)} · unavailable</span>'
    return ' '.join(_link(identifier if len(matches)==1 else row.sequence_id,
        target_url(base,'Protein dossier',protein=row.sequence_id),'protein',
        f'{row.sequence_id} · {row.family} · {row.audit_classification}') for row in matches.itertuples())


def family_links(families,candidates,base,labels=None):
    links=[]
    for family in families:
        available=available_families((family,),candidates)
        links.extend(_link((labels or {}).get(family,name.replace('_',' ')),target_url(base,'Components',family=name),'family','Open family candidate catalogue') for name in available)
        if not available:links.append(f'<span class="research-unavailable">{escape(family)} · unavailable</span>')
    return ' '.join(links)


def available_families(families,candidates):
    from library_refresh import family_key
    wanted={family_key(alias) for family in families for alias in FAMILY_ALIASES.get(family,(family,))}
    return sorted(name for name in set(candidates.family) if family_key(name) in wanted)


def rich_text(text,candidates,base):
    """Safe inline links to exact records, orthogroups and the brief's original DOIs."""
    protein_pattern=r'(?:[A-Za-z]+__)?(?:Smp_|MS3_|EWB00_|SBOV2_|SCUR1_|SINT2_|SRDH2_)\d+(?:\.\d+)?'
    pattern=CITATION_PATTERN+r'|`?(?:OG\d{7}|'+protein_pattern+r')`?'
    parts=[];end=0;groups=set(candidates.orthogroup)
    for match in re.finditer(pattern,text):
        parts.append(escape(text[end:match.start()]))
        token=match[0].strip('`')
        if match[1] or match[3]:
            label,url=(match[1],match[2]) if match[1] else (match[3],match[4])
            parts.append(f'<a href="{escape(url,quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)} ↗</a>')
        elif re.fullmatch(protein_pattern,token):parts.append(protein_links(token,candidates,base))
        elif token in groups:parts.append(_link(token,target_url(base,'Orthology',orthogroup=token),'orthogroup','Open orthogroup assignments and members'))
        else:parts.append(f'<span class="research-unavailable">{escape(token)} · unavailable</span>')
        end=match.end()
    from scientific_text import scientific_html
    parts.append(escape(text[end:]));return scientific_html(''.join(parts))


def metric_comparison(metric,candidates):
    aliases=set(available_families(metric['families'],candidates))
    family_scope=candidates.family.isin(aliases)
    if metric.get('group_scope'):family_scope=family_scope|candidates.orthogroup.isin(metric['group_scope'])
    if metric.get('hypothesis_field') in candidates:
        from library_refresh import family_key
        wanted={family_key(alias) for family in metric['families'] for alias in FAMILY_ALIASES.get(family,(family,))}
        family_scope=family_scope|candidates[metric['hypothesis_field']].map(family_key).isin(wanted)
    if metric['classification']=='Supported':
        from functional_categories import supported_mask
        status=supported_mask(candidates)
    else:status=candidates.audit_classification.eq(metric['classification'])
    selected=candidates[family_scope & status]
    live=selected.loc[selected.orthogroup.ne(''),'orthogroup'].nunique() if metric.get('orthogroups') else selected.sequence_id.nunique()
    return dict(label=metric['label'],brief=metric['count'],live=int(live),matches=metric['count']==live)


def comparisons(brief,candidates):
    rows=[]
    for feature in brief['features']:
        rows.extend(dict(category=feature['label'],**metric_comparison(m,candidates)) for m in feature['metrics'])
    for row in brief['additional']:
        rows.append(dict(category=row['Candidate family'],**metric_comparison(dict(label='Supported candidates',count=row['count'],families=row['families'],group_scope=row.get('orthogroups',()),classification='Supported'),candidates)))
    return rows


def _reference_links(registry,families,candidates):
    from literature import evidence_for
    if not registry:
        return ''
    refs=registry['references']
    ids=sorted({link['reference_id'] for family in available_families(families,candidates)
                for link in evidence_for(registry,family)})
    return ' '.join(f'<a href="{escape(refs[rid]["doi_url"])}" target="_blank" rel="noopener">{rid}</a>' for rid in ids)


def priority_trace(brief,candidates,registry):
    """Connect the brief's representatives and orthogroups to scoped registry evidence."""
    from literature import evidence_for
    targets=[(feature['label'],feature['proteins'],feature['orthogroups'],feature['families'])
             for feature in brief['features']]
    targets.extend((row['Candidate family'],re.findall(r'(?:[A-Za-z]+__)?(?:Smp|SBOV2)_\d+',row['Representative S. mansoni IDs']),
                    row['orthogroups'],row['families']) for row in brief['additional'])
    for row in brief['roadmap']:
        label=row['Candidate or orthogroup']
        targets.append((label,re.findall(r'(?:[A-Za-z]+__)?(?:Smp|SBOV2)_\d+',label),re.findall(r'OG\d{7}',label),()))
    rows=[]
    for label,proteins,groups,families in targets:
        ids={pid for accession in proteins for pid in protein_matches(candidates,accession).sequence_id}
        scoped=candidates[candidates.sequence_id.isin(ids)|candidates.orthogroup.isin(groups)]
        if scoped.empty and families:
            scoped=candidates[candidates.family.isin(available_families(families,candidates))]
        for row in scoped.drop_duplicates('sequence_id').itertuples():
            links=evidence_for(registry,row.family,row.sequence_id)
            for link in links or [{}]:
                rid=link.get('reference_id','')
                rows.append(dict(priority=label,protein_id=row.sequence_id,family=row.family,
                                 priority_scope='Representative accession' if row.sequence_id in ids else
                                 'Orthogroup context' if row.orthogroup in groups else 'Family context',
                                 orthogroup=row.orthogroup,grade=row.grade,support=row.family_support_level,
                                 reference_id=rid,match_level=link.get('match_level',''),
                                 doi_url=registry['references'].get(rid,{}).get('doi_url',''),
                                 evidence_note=link.get('note','')))
    return rows


def feature_card(feature,candidates,base,registry=None):
    metrics=''
    for metric in feature['metrics']:
        comparison=metric_comparison(metric,candidates)
        badge=metric['classification'].lower()
        diff=f'<span class="research-difference">Catalogue: {comparison["live"]:,} · differs from brief</span>' if not comparison['matches'] else ''
        metrics+=f'<div class="research-metric {badge}"><strong>{metric["count"]:,}</strong><span>{escape(metric["label"])}</span>{diff}</div>'
    evidence=''.join('<p>'+rich_text(p,candidates,base)+'</p>' for p in feature['evidence'])
    for row in feature['assignments']:
        evidence+='<p>'+rich_text(' · '.join(row.values()),candidates,base)+'</p>'
    return (f'<article class="research-card" aria-label="{escape(feature["label"])}">'
        f'<h3>{escape(feature["label"])}</h3><div class="research-metrics">{metrics}</div>'
        f'<p class="research-objective">{escape(feature["objective"])}</p>'
        f'<div class="research-card-label">Explore families</div><div class="research-links">{family_links(feature["families"],candidates,base)}</div>'
        f'<div class="research-card-label">Key orthogroups</div><div class="research-links">{rich_text(" · ".join(feature["orthogroups"]),candidates,base)}</div>'
        f'<div class="research-card-label">Representative proteins · <em>S. mansoni</em></div><div class="research-links">{rich_text(" · ".join(feature["proteins"]),candidates,base)}</div>'
        f'<div class="research-next"><span>Next investigation</span><p>{escape(feature["next"])}</p></div>'
        f'<details><summary>Evidence & interpretation</summary><div class="research-evidence"><span class="research-tag published">Published evidence / research context</span>{evidence}<p>{_reference_links(registry,feature["families"],candidates)}</p></div></details></article>')


def research_priorities_panel(candidates,base,source,registry=None):
    import pandas as pd
    import streamlit as st
    if not source.exists():
        st.info('Research priorities will be updated when Target_prioritization.md is available.');return
    try:brief=load_brief(source)
    except (ValueError,StopIteration) as error:
        st.warning('The research-priority brief needs a format update: '+str(error));return
    st.markdown('<section class="research-intro"><h2 id="research-priorities">Research Priorities & Target Discovery</h2><p>'+rich_text(brief.get('overview',OVERVIEW),candidates,base)+'</p></section>',unsafe_allow_html=True)
    st.markdown('<div class="research-legend"><span class="research-tag supported">Specific or broad family support</span><span class="research-tag provisional">Ambiguous or provisional assignment</span><span class="research-tag unassigned">Unresolved assignment</span><span class="research-tag published">Published evidence</span><span class="research-tag proposed">Proposed research</span></div>',unsafe_allow_html=True)
    st.caption('Family assignments support computational prioritization. Published findings apply to the named proteins or antigens; candidate-family membership does not establish vaccine efficacy, drug activity or biological essentiality. Counts below cover the complete catalogue, independently of sidebar filters.')
    checks=comparisons(brief,candidates)
    differences=[r for r in checks if not r['matches']]
    if differences:st.warning(f'{len(differences)} research-brief count(s) differ from the live catalogue. Both values are shown; see Count reconciliation below.')
    featured,framework,roadmap=st.tabs(['Featured priorities','Target-selection framework','Experimental roadmap'])
    with featured:
        st.markdown('<div class="research-grid">'+''.join(feature_card(f,candidates,base,registry) for f in brief['features'])+'</div>',unsafe_allow_html=True)
        with st.expander('Additional Adhesome Targets for Functional Investigation'):
            st.caption('Functional and therapeutic research candidates. These family assignments do not establish experimentally confirmed drug targets.')
            cards=[]
            for row in brief['additional']:
                check=next(r for r in checks if r['category']==row['Candidate family'])
                diff=f'<p class="research-difference">Live catalogue: {check["live"]} supported candidates; brief: {check["brief"]}.</p>' if not check['matches'] else ''
                count_label=row['Supported proteins'] if 'supported' in row['Supported proteins'].lower() else row['Supported proteins']+' supported candidates'
                cards.append('<article class="research-additional"><h4>'+escape(row['Candidate family'])+'</h4><span class="research-tag supported">'+escape(count_label)+'</span>'+diff+
                    '<p>'+rich_text(row['Priority and rationale'],candidates,base)+'</p><div class="research-card-label">Principal validation challenge</div><p>'+escape(row['challenge'])+'</p><div class="research-links">'+family_links(row['families'],candidates,base)+'</div><div class="research-links">'+rich_text(row['Representative S. mansoni IDs'],candidates,base)+'</div><p>'+_reference_links(registry,row['families'],candidates)+'</p></article>')
            st.markdown('<div class="research-additional-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)
            if brief.get('additional_evidence'):
                st.markdown('#### Evidence and expanded family priorities')
                st.markdown(rich_text(brief['additional_evidence'],candidates,base),unsafe_allow_html=True)
    with framework:
        st.markdown('#### Match the evidence to the development objective')
        mode=st.radio('Compare target-development routes',['Side by side','Vaccine / antibody candidates','Small-molecule drug candidates'],horizontal=True,key='research_framework')
        columns=['Evaluation criterion']
        if mode!='Small-molecule drug candidates':columns.append('Vaccine/antibody candidate')
        if mode!='Vaccine / antibody candidates':columns.append('Small-molecule drug candidate')
        headings={'Accessibility':'Target accessibility','Selectivity':'Host–parasite selectivity','Feasibility':'Experimental feasibility'}
        header=''.join('<th scope="col">'+escape(c)+'</th>' for c in columns)
        rows=''.join('<tr>'+''.join('<th scope="row">'+escape(headings.get(row[c],row[c]))+'</th>' if c==columns[0] else '<td>'+escape(row[c])+'</td>' for c in columns)+'</tr>' for row in brief['framework'])
        st.markdown('<div class="research-matrix"><table><thead><tr>'+header+'</tr></thead><tbody>'+rows+'</tbody></table></div>',unsafe_allow_html=True)
        st.caption('A qualitative decision framework; no new numerical priority score is calculated. The existing Components prioritization analysis remains available.')
        if brief.get('framework_text'):st.markdown(rich_text(brief['framework_text'],candidates,base),unsafe_allow_html=True)
    with roadmap:
        st.markdown('#### From Computational Candidates to Experimental Validation')
        st.caption('Proposed first investigations from the research brief. These steps are a research plan, not completed experimental results.')
        if brief.get('repeated_roadmap_rows'):st.caption(f'{brief["repeated_roadmap_rows"]} repeated roadmap entry displayed once; the complete original brief is available for download.')
        items=[]
        for i,row in enumerate(brief['roadmap'],1):
            target=rich_text(row['Candidate or orthogroup'],candidates,base)
            name=row['Candidate or orthogroup']
            if name.endswith(' representatives'):
                families=tuple(name.removesuffix(' representatives').split('/'))
                if all(available_families((family,),candidates) for family in families):target=family_links(families,candidates,base)+' representatives'
            items.append(f'<article class="research-step"><span class="research-step-number">{i:02}</span><div><div class="research-card-label">{escape(row["Development objective"])}</div><h4>{target}</h4><p>{escape(row["First decisive experiment or analysis"])}</p><span class="research-tag proposed">Proposed investigation</span></div></article>')
        st.markdown('<div class="research-roadmap">'+''.join(items)+'</div>',unsafe_allow_html=True)
    with st.expander('Research references'+(' & count mismatches' if differences else '')):
        st.caption('Live counts use unique protein IDs and the audited support designations. Specific and broad family support contribute to the supported totals. Orthogroup counts use supported members only.')
        for ref in brief['references']:st.markdown(f'[{ref["label"]}]({ref["url"]})')
        if differences:
            st.dataframe(pd.DataFrame(differences).drop(columns='matches').rename(columns={'category':'Research category','label':'Measure','brief':'Research brief','live':'Live catalogue'}),hide_index=True,width='stretch')
        st.download_button('Download research-priority brief',source.read_text(encoding='utf-8-sig'),source.name,'text/markdown')
        if registry:
            from literature import tsv
            st.download_button('Download candidate-to-reference traceability',tsv(priority_trace(brief,candidates,registry)),
                               'priority_reference_trace.tsv','text/tab-separated-values')
