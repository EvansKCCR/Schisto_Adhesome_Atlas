"""Scientific emphasis, safe HTML, raw plotting data and map destinations."""
from bootstrap import ATLAS_ROOT
from html.parser import HTMLParser
from urllib.parse import urlsplit,parse_qs
import pandas as pd
import plotly.express as px

from scientific_text import markdown_text,scientific_html,inline_html,register_species
from navigation import HYPOTHESIS_PAGE,hypothesis_url,PAGES
from research_priorities import apply_target_route,rich_text
from figure_exports import legible_figure


def main():
    assert markdown_text('S. mansoni and Schistosoma japonicum')=='*S. mansoni* and *Schistosoma japonicum*'
    assert markdown_text('*S. mansoni* and `S. mansoni`')=='*S. mansoni* and `S. mansoni`'
    assert markdown_text('**S. mansoni**')=='***S. mansoni***'
    html=scientific_html('<p>**Strong <a href="/gene?text=**raw**">gene</a> evidence** in *S. mansoni*.</p>')
    assert '<strong>Strong <a' in html and 'evidence</strong>' in html
    assert '<em>S. mansoni</em>' in html and '*<em>' not in html
    assert 'href="/gene?text=**raw**"' in html
    assert scientific_html('<code>**literal S. mansoni**</code>')=='<code>**literal S. mansoni**</code>'
    assert scientific_html('<p><em>S. mansoni</em></p>')=='<p><em>S. mansoni</em></p>'
    assert '&lt;script&gt;' in inline_html('<script>alert(1)</script> **bold** S. mansoni')
    assert '<strong>bold</strong>' in inline_html('**bold**')
    raw=['Schistosoma mansoni','Schistosoma haematobium','Schistosoma japonicum']
    fig=px.bar(x=raw,y=[2,3,4],color=raw,title='**Comparative** Schistosoma atlas')
    before=[tuple(trace.x) for trace in fig.data];legible_figure(fig)
    assert before==[tuple(trace.x) for trace in fig.data]
    assert '<b>Comparative</b>' in fig.layout.title.text
    assert all('<i>' in text for text in fig.layout.xaxis.ticktext)
    assert all('<i>' in trace.name for trace in fig.data)
    assert len(PAGES)==11 and PAGES[1]==HYPOTHESIS_PAGE
    candidates=pd.DataFrame([dict(sequence_id='Sman__Smp_1',family='talin',orthogroup='OG0000001',audit_classification='Supported')])
    state={};apply_target_route(candidates,{'view':'Introduction','protein':'Sman__Smp_1'},state)
    assert state['atlas_page']==HYPOTHESIS_PAGE and state['map_candidate']=='Sman__Smp_1'
    state={};apply_target_route(candidates,{'view':'Introduction'},state);assert state['atlas_page']=='Introduction'
    assert parse_qs(urlsplit(hypothesis_url('https://atlas.example/app','Sman__Smp_1')).query)['view']==[HYPOTHESIS_PAGE]
    assert parse_qs(urlsplit(hypothesis_url('https://atlas.example/app')).query)['view']==[HYPOTHESIS_PAGE]
    linked=rich_text('**Protein Smp_1 in S. mansoni**',candidates,'https://atlas.example/')
    assert '**' not in linked and '<strong>' in linked and '<em>S. mansoni</em>' in linked
    print('PASS bold across links, scientific italics, existing emphasis/code, safe HTML, unchanged plot data, italic figure labels, 11 destinations, new map links and legacy bookmarks.',flush=True)


if __name__=='__main__':main()
