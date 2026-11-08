"""Presentation-only emphasis and scientific-name formatting.

Raw identifiers, tables, exports and source files retain their original values.
Canvas typography covers native data-grid cells/headers without replacing grids.
"""
from functools import wraps
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

_NAMES={
 'Schistosoma '+epithet for epithet in ['haematobium','japonicum','mansoni','bovis','curassoni',
 'intercalatum','rodhaini','guineensis','mekongi','malayensis','mattheei','spindale','indicum',
 'nasale','incognitum','hippopotami','margrebowiei','leiperi','edwardiense']}
_NAMES.update(['Fasciola hepatica','Fasciola gigantica','Taenia solium','Taenia saginata',
 'Taenia asiatica','Echinococcus granulosus','Echinococcus multilocularis','Hymenolepis microstoma',
 'Hymenolepis nana','Hymenolepis diminuta','Clonorchis sinensis','Opisthorchis viverrini',
 'Opisthorchis felineus','Fasciolopsis buski','Trichinella spiralis','Strongyloides stercoralis',
 'Strongyloides ratti','Haemonchus contortus','Ancylostoma duodenale','Ancylostoma ceylanicum',
 'Necator americanus','Ascaris suum','Ascaris lumbricoides','Trichuris trichiura','Trichuris muris',
 'Brugia malayi','Wuchereria bancrofti','Onchocerca volvulus','Plasmodium falciparum',
 'Plasmodium vivax','Toxoplasma gondii','Trypanosoma brucei','Trypanosoma cruzi',
 'Leishmania major','Leishmania donovani','Giardia intestinalis','Giardia lamblia',
 'Entamoeba histolytica','Cryptosporidium parvum','Homo sapiens','Homo sapien',
 'Mus musculus','Rattus norvegicus','Danio rerio','Danio reri','Xenopus laevis',
 'Xenopus tropicalis','Drosophila melanogaster','Caenorhabditis elegans','Canis familiaris',
 'Pan troglodytes','Ciona intestinalis','Gallus gallus'])
_BOLD=re.compile(r'\*\*(?=\S)(.+?)(?<=\S)\*\*',re.S)
_PROTECTED_MD=re.compile(r'(`+)[\s\S]*?\1|(\${1,2})[\s\S]*?\2|(?:https?|ftp)://[^\s<>)]+|(?<!\*)\*[^*\n]+\*(?!\*)|(?<!_)_[^_\n]+_(?!_)|<[^>]*>')


def register_species(names=()):
    previous=len(_NAMES)
    for name in names:
        if isinstance(name,str) and re.fullmatch(r'[A-Z][a-z]+ [a-z][a-z-]+',name.strip()):_NAMES.add(name.strip())
    labels=set(_NAMES)|{name[0]+'. '+name.split(' ',1)[1] for name in _NAMES}|{'Schistosoma'}
    parts=[re.escape(name).replace(r'\ ',r'\s+').replace(r'\.\s+',r'\.\s*') for name in sorted(labels,key=lambda n:(-len(n),n))]
    global SPECIES_PATTERN,SPECIES_RE
    SPECIES_PATTERN=r'(?<![A-Za-z0-9_])(?:'+'|'.join(parts)+r')(?![A-Za-z0-9_])'
    SPECIES_RE=re.compile(SPECIES_PATTERN,re.I)
    return len(_NAMES)!=previous


register_species()


def markdown_text(value):
    """Add scientific italics while retaining Markdown emphasis/code and identifiers."""
    if not isinstance(value,str) or not SPECIES_RE.search(value):return value
    pieces=[];end=0
    for match in _PROTECTED_MD.finditer(value):
        pieces.append(SPECIES_RE.sub(lambda m:'*'+m[0]+'*',value[end:match.start()]))
        pieces.append(match[0]);end=match.end()
    pieces.append(SPECIES_RE.sub(lambda m:'*'+m[0]+'*',value[end:]));return ''.join(pieces)


class _ScientificHTML(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=False);self.parts=[];self.stack=[]
    def handle_starttag(self,tag,attrs):
        self.parts.append(self.get_starttag_text())
        if tag not in {'br','hr','img','input','meta','link','source','wbr'}:self.stack.append(tag)
    def handle_startendtag(self,tag,attrs):self.parts.append(self.get_starttag_text())
    def handle_endtag(self,tag):
        self.parts.append('</'+tag+'>')
        if tag in self.stack:self.stack=self.stack[:len(self.stack)-1-self.stack[::-1].index(tag)]
    def handle_data(self,data):
        if not set(self.stack)&{'em','i','script','style','code','pre','svg','textarea'}:
            data=SPECIES_RE.sub(lambda m:'<em>'+m[0]+'</em>',data)
        self.parts.append(data)
    def handle_entityref(self,name):self.parts.append('&'+name+';')
    def handle_charref(self,name):self.parts.append('&#'+name+';')
    def handle_comment(self,data):self.parts.append('<!--'+data+'-->')
    def handle_decl(self,data):self.parts.append('<!'+data+'>')


def scientific_html(value):
    """Format safe/generated HTML, including emphasis spanning an inline link."""
    if not isinstance(value,str) or not (_BOLD.search(value) or SPECIES_RE.search(value)):return value
    protected=[]
    def hold(match):
        protected.append(match[0]);return '\x00ATLAS'+str(len(protected)-1)+'\x00'
    text=re.sub(r'<(script|style|pre|code|svg)\b[^>]*>[\s\S]*?</\1\s*>',hold,value,flags=re.I)
    text=re.sub(r'<[^>]+>',hold,text)
    text=re.sub(r'\*\*\*(?=\S)(.+?)(?<=\S)\*\*\*',lambda m:'<strong><em>'+m[1]+'</em></strong>',text,flags=re.S)
    text=_BOLD.sub(lambda m:'<strong>'+m[1]+'</strong>',text)
    text=re.sub(r'(?<!\*)\*(?=\S)([^*\n]+?)(?<=\S)\*(?!\*)',lambda m:'<em>'+m[1]+'</em>',text)
    for i,raw in reversed(list(enumerate(protected))):text=text.replace('\x00ATLAS'+str(i)+'\x00',raw)
    parser=_ScientificHTML();parser.feed(text);parser.close();return ''.join(parser.parts)


def inline_html(value):return scientific_html(escape(str(value)))


def plotly_text(value):
    return scientific_html(value).replace('<strong>','<b>').replace('</strong>','</b>').replace('<em>','<i>').replace('</em>','</i>') if isinstance(value,str) else value


def javascript(mode='owned'):
    script=Path(__file__).with_name('scientific_typography.js').read_text(encoding='utf-8')
    return script.replace('__ATLAS_SPECIES_PATTERN__',json.dumps(SPECIES_PATTERN)).replace('__ATLAS_TYPOGRAPHY_MODE__',json.dumps(mode))


def owned_assets():return '<script>'+javascript()+'</script>'


def install_streamlit():
    """Format display strings before native Markdown rendering; never options/data."""
    import streamlit as st
    from streamlit.delta_generator import DeltaGenerator
    methods=['markdown','caption','header','subheader','title','info','warning','error','success',
        'expander','button','link_button','download_button','radio','checkbox','toggle','selectbox',
        'multiselect','text_input','text_area','metric']
    for name in methods:
        native=getattr(DeltaGenerator,name)
        if not getattr(native,'_atlas_typography',False):
            def make(original,method):
                @wraps(original)
                def formatted(self,*args,**kwargs):
                    key='body' if method in {'markdown','caption','info','warning','error','success'} else 'label' if method in {'button','link_button','download_button','radio','checkbox','toggle','selectbox','multiselect','text_input','text_area','metric','expander'} else 'body'
                    formatter=scientific_html if method=='markdown' and kwargs.get('unsafe_allow_html',False) else markdown_text
                    if args and isinstance(args[0],str):args=(formatter(args[0]),)+args[1:]
                    elif isinstance(kwargs.get(key),str):kwargs={**kwargs,key:formatter(kwargs[key])}
                    return original(self,*args,**kwargs)
                formatted._atlas_typography=True
                return formatted
            setattr(DeltaGenerator,name,make(native,name))
        setattr(st,name,getattr(st._main,name))
    native=DeltaGenerator.write
    if not getattr(native,'_atlas_typography',False):
        @wraps(native)
        def write(self,*args,**kwargs):return native(self,*(markdown_text(v) if isinstance(v,str) else v for v in args),**kwargs)
        write._atlas_typography=True;DeltaGenerator.write=write
    st.write=st._main.write


_BROWSER_COMPONENT=None

def install_browser_typography():
    """Mount trusted presentation code through Streamlit's in-page component API."""
    import hashlib
    import streamlit.components.v2 as components
    global _BROWSER_COMPONENT
    if _BROWSER_COMPONENT is None:
        source=(Path(__file__).with_name('scientific_typography.js').read_text(encoding='utf-8')
                .replace('__ATLAS_SPECIES_PATTERN__','component.data')
                .replace('__ATLAS_TYPOGRAPHY_MODE__',json.dumps('react')))
        _BROWSER_COMPONENT=components.component('atlas_scientific_typography',
            js='export default function(component){'+source+'}',isolate_styles=False)
    _BROWSER_COMPONENT(data=SPECIES_PATTERN,key='atlas_typography_'+hashlib.sha256(SPECIES_PATTERN.encode()).hexdigest()[:12],height=0)
