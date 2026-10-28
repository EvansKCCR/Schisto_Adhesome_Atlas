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


def _tabular(text, first_header):
    """Read the brief's tab-separated scientific tables, without altering their cells."""
    lines=text.splitlines()
    start=next((i for i,line in enumerate(lines) if line.startswith(first_header+'\t')),None)
    if start is None:
        raise ValueError('Missing research-priority table: '+first_header)
    headers=lines[start].split('\t');rows=[]
    for line in lines[start+1:]:
        if not line.strip() or '\t' not in line:break
        values=line.split('\t')
        if len(values)!=len(headers):raise ValueError('Incomplete research-priority table row: '+line)
        rows.append(dict(zip(headers,values)))
    return rows


def _number(value):
    if value.isdigit():return int(value)
    words='zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split()
    if value.lower() not in words:raise ValueError('Unrecognized count in the research brief: '+value)
    return words.index(value.lower())


def load_brief(path):
    text=Path(path).read_text(encoding='utf-8-sig')
    chunks=re.split(r'^##\s+\*\*Target\s+\d+[^\n]*\n',text,flags=re.M)[1:]
    if len(chunks)!=3:raise ValueError('Expected three featured Target headings in Target_prioritization.md.')
    # The third section ends where the additional-family table begins.
    chunks[-1]=chunks[-1].split('2. **Additional candidates')[0]
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
            assignments=_tabular(chunk,'Protein ID')
        else:
            found=re.search(r'(\d+) supported candidates across (\w+) orthogroups',count_line)
            if not found:raise ValueError('Cannot read candidate/orthogroup counts in the priority brief.')
            group_count=_number(found[2])
            metrics=[dict(label='Supported candidates',count=int(found[1]),families=spec['families'],classification='Supported'),
                     dict(label='Supported orthogroups',count=group_count,families=spec['families'],classification='Supported',orthogroups=True)]
            assignments=[]
        # Retain the scientific prose and every reference, including the named calpain bullets.
        evidence=[]
        for line in chunk.splitlines():
            if not line.strip() or '\t' in line or line.removeprefix('- ')==count_line or line.startswith('- Key orthogroups:') or line.startswith('- Representative') or line.startswith('- Three S. mansoni'):continue
            evidence.append(line.removeprefix('- '))
        features.append({**spec,'metrics':metrics,'count_text':count_line,
            'orthogroups':list(dict.fromkeys(re.findall(r'OG\d{7}',chunk))),
            'proteins':list(dict.fromkeys(re.findall(r'Smp_\d+',chunk))),
            'evidence':evidence,'assignments':assignments})
    additional=_tabular(text,'Candidate family')
    for row in additional:
        row['families']=FAMILY_JOINS.get(row['Candidate family'],())
        row['count']=int(re.search(r'\d+',row['Supported proteins'])[0])
        row['challenge']=CHALLENGES.get(row['Candidate family'],'No additional information present in the current library.')
    references=[]
    for label,url in re.findall(r'\(([^()]+)\)\[(https://doi\.org/[^\]]+)\]',text):
        if url not in [r['url'] for r in references]:references.append(dict(label=label,url=url))
    return dict(features=features,additional=additional,framework=_tabular(text,'Evaluation criterion'),
                roadmap=_tabular(text,'Candidate or orthogroup'),references=references)


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
    route=(view,protein,family,group,params.get('workspace',''))
    if state.get('atlas_route')==route:return
    state['atlas_route']=route
    if view in {'Introduction','Protein dossier','Components','Orthology','Phylogeny'}:state['atlas_page']=view
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
    available=set(candidates.family)
    return list(dict.fromkeys(alias for family in families for alias in FAMILY_ALIASES.get(family,(family,)) if alias in available))


def rich_text(text,candidates,base):
    """Safe inline links to exact records, orthogroups and the brief's original DOIs."""
    pattern=r'\(([^()]+)\)\[(https://doi\.org/[^\]]+)\]|OG\d{7}|Smp_\d+'
    parts=[];end=0;groups=set(candidates.orthogroup)
    for match in re.finditer(pattern,text):
        parts.append(escape(text[end:match.start()]))
        if match[1]:parts.append(f'<a href="{escape(match[2],quote=True)}" target="_blank" rel="noopener noreferrer">{escape(match[1])} ↗</a>')
        elif match[0].startswith('Smp_'):parts.append(protein_links(match[0],candidates,base))
        elif match[0] in groups:parts.append(_link(match[0],target_url(base,'Orthology',orthogroup=match[0]),'orthogroup','Open orthogroup assignments and members'))
        else:parts.append(f'<span class="research-unavailable">{escape(match[0])} · unavailable</span>')
        end=match.end()
    parts.append(escape(text[end:]));return ''.join(parts)


def metric_comparison(metric,candidates):
    aliases={alias for family in metric['families'] for alias in FAMILY_ALIASES.get(family,(family,))}
    family_scope=candidates.family.isin(aliases)
    if metric.get('hypothesis_field') in candidates:
        family_scope=family_scope|candidates[metric['hypothesis_field']].isin(aliases)
    selected=candidates[family_scope & candidates.audit_classification.eq(metric['classification'])]
    live=selected.loc[selected.orthogroup.ne(''),'orthogroup'].nunique() if metric.get('orthogroups') else selected.sequence_id.nunique()
    return dict(label=metric['label'],brief=metric['count'],live=int(live),matches=metric['count']==live)


def comparisons(brief,candidates):
    rows=[]
    for feature in brief['features']:
        rows.extend(dict(category=feature['label'],**metric_comparison(m,candidates)) for m in feature['metrics'])
    for row in brief['additional']:
        rows.append(dict(category=row['Candidate family'],**metric_comparison(dict(label='Supported candidates',count=row['count'],families=row['families'],classification='Supported'),candidates)))
    return rows


def feature_card(feature,candidates,base):
    metrics=''
    for metric in feature['metrics']:
        comparison=metric_comparison(metric,candidates)
        badge=metric['classification'].lower()
        diff=f'<span class="research-difference">Catalogue: {comparison["live"]:,} · differs from brief</span>' if not comparison['matches'] else ''
        metrics+=f'<div class="research-metric {badge}"><strong>{metric["count"]:,}</strong><span>{escape(metric["label"])}</span>{diff}</div>'
    evidence=''.join('<p>'+rich_text(p,candidates,base)+'</p>' for p in feature['evidence'])
    for row in feature['assignments']:
        evidence+='<p>'+rich_text(' · '.join(row.values()),candidates,base)+'</p>'
    return (f'<article class="research-card" aria-label="{escape(feature["label"])}"><div class="research-card-kicker">Research priority · {escape(feature["key"])}</div>'
        f'<h3>{escape(feature["label"])}</h3><div class="research-metrics">{metrics}</div>'
        f'<p class="research-objective">{escape(feature["objective"])}</p>'
        f'<div class="research-card-label">Explore families</div><div class="research-links">{family_links(feature["families"],candidates,base)}</div>'
        f'<div class="research-card-label">Key orthogroups</div><div class="research-links">{rich_text(" · ".join(feature["orthogroups"]),candidates,base)}</div>'
        f'<div class="research-card-label">Representative proteins · S. mansoni</div><div class="research-links">{rich_text(" · ".join(feature["proteins"]),candidates,base)}</div>'
        f'<div class="research-next"><span>Next investigation</span><p>{escape(feature["next"])}</p></div>'
        f'<details><summary>Evidence & interpretation</summary><div class="research-evidence"><span class="research-tag published">Published evidence / research context</span>{evidence}</div></details></article>')


def research_priorities_panel(candidates,base,source):
    import pandas as pd
    import streamlit as st
    if not source.exists():
        st.info('Research priorities will be updated when Target_prioritization.md is available.');return
    try:brief=load_brief(source)
    except (ValueError,StopIteration) as error:
        st.warning('The research-priority brief needs a format update: '+str(error));return
    st.markdown('<section class="research-intro"><div class="atlas-section-kicker">Comparative evidence → testable research</div><h2 id="research-priorities">Research Priorities & Target Discovery</h2><p>'+escape(OVERVIEW)+'</p></section>',unsafe_allow_html=True)
    st.markdown('<div class="research-legend"><span class="research-tag supported">Supported computational annotation · A/B</span><span class="research-tag provisional">Provisional assignment · C</span><span class="research-tag unassigned">Unassigned · D</span><span class="research-tag published">Published experimental evidence</span><span class="research-tag proposed">Proposed research</span></div>',unsafe_allow_html=True)
    st.caption('Family assignments support computational prioritization. Published findings apply to the named proteins or antigens; candidate-family membership does not establish vaccine efficacy, drug activity or biological essentiality. Counts below cover the complete catalogue, independently of sidebar filters.')
    checks=comparisons(brief,candidates)
    differences=[r for r in checks if not r['matches']]
    if differences:st.warning(f'{len(differences)} research-brief count(s) differ from the live catalogue. Both values are shown; see Count reconciliation below.')
    featured,framework,roadmap=st.tabs(['Featured priorities','Target-selection framework','Experimental roadmap'])
    with featured:
        st.markdown('<div class="research-grid">'+''.join(feature_card(f,candidates,base) for f in brief['features'])+'</div>',unsafe_allow_html=True)
        with st.expander('Additional Adhesome Targets for Functional Investigation'):
            st.caption('Functional and therapeutic research candidates. These family assignments do not establish experimentally confirmed drug targets.')
            cards=[]
            for row in brief['additional']:
                check=next(r for r in checks if r['category']==row['Candidate family'])
                diff=f'<p class="research-difference">Live catalogue: {check["live"]} supported candidates; brief: {check["brief"]}.</p>' if not check['matches'] else ''
                count_label=row['Supported proteins'] if 'supported' in row['Supported proteins'].lower() else row['Supported proteins']+' supported candidates'
                cards.append('<article class="research-additional"><h4>'+escape(row['Candidate family'])+'</h4><span class="research-tag supported">'+escape(count_label)+'</span>'+diff+
                    '<p>'+rich_text(row['Priority and rationale'],candidates,base)+'</p><div class="research-card-label">Principal validation challenge</div><p>'+escape(row['challenge'])+'</p><div class="research-links">'+family_links(row['families'],candidates,base)+'</div><div class="research-links">'+rich_text(row['Representative S. mansoni IDs'],candidates,base)+'</div></article>')
            st.markdown('<div class="research-additional-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)
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
    with roadmap:
        st.markdown('#### From Computational Candidates to Experimental Validation')
        st.caption('Proposed first investigations from the research brief. These steps are a research plan, not completed experimental results.')
        items=[]
        for i,row in enumerate(brief['roadmap'],1):
            target=rich_text(row['Candidate or orthogroup'],candidates,base)
            if i==len(brief['roadmap']):target=family_links(('FAK','ILK','talin','kindlin'),candidates,base)
            items.append(f'<article class="research-step"><span class="research-step-number">{i:02}</span><div><div class="research-card-label">{escape(row["Development objective"])}</div><h4>{target}</h4><p>{escape(row["First decisive experiment or analysis"])}</p><span class="research-tag proposed">Proposed investigation</span></div></article>')
        st.markdown('<div class="research-roadmap">'+''.join(items)+'</div>',unsafe_allow_html=True)
    with st.expander('Research references'+(' & count mismatches' if differences else '')):
        st.caption('Scientific content: Target_prioritization.md. Brief counts are preserved; live counts use unique protein IDs and A/B = Supported, C = Provisional, D = Unassigned. Unassigned integrin hypotheses are counted from the recorded stage-1 hypothesis without assigning family membership. Orthogroup counts use supported members only.')
        for ref in brief['references']:st.markdown(f'[{ref["label"]}]({ref["url"]})')
        if differences:
            st.dataframe(pd.DataFrame(differences).drop(columns='matches').rename(columns={'category':'Research category','label':'Measure','brief':'Research brief','live':'Live catalogue'}),hide_index=True,width='stretch')
        st.download_button('Download research-priority brief',source.read_text(encoding='utf-8-sig'),source.name,'text/markdown')
