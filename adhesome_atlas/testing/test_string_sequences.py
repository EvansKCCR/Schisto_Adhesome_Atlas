"""STRING sequence mapping, failure recovery, alignment evidence and exact joins."""
from bootstrap import ATLAS_ROOT
import json,sys,time
from pathlib import Path
from unittest.mock import patch
import string_fetch as sf


def hit(query,sid,identity=100,score=500,evalue=1e-80):
    return {'querySequenceName':query,'hitStringId':'6183.'+sid,'hitNcbiTaxonId':'6183',
            'hitPreferredName':sid,'identity':identity,'bitscore':score,'E-value':evalue}


def main():
    sequences={'a':'MALWMRLLPLL','b':'MACDEFGHIK','c':'MNPQRSTVWY','d':'MKKKKKKKKK','missing':''}
    hits=[hit('a','A'),hit('a','low',identity=25,score=50),hit('b','B'),hit('b','B2',score=490),hit('c','C',identity=50)]
    mapped,states,rows=sf.sequence_matches(json.dumps(hits),list(sequences),6183)
    assert mapped=={'a':'6183.A'} and len(rows)==len(hits)
    assert states['b']=='Ambiguous sequence representatives' and states['c']=='No sequence hit passes mapping thresholds' and states['d']=='No sequence hits'
    assert sum(r['decision']=='Selected sequence representative' for r in rows)==1
    for bad in [[hit('unknown','A')],[{**hit('a','A'),'hitStringId':'9606.A'}],[{**hit('a','A'),'identity':101}]]:
        try:sf.sequence_matches(json.dumps(bad),['a'],6183)
        except ValueError:pass
        else:raise AssertionError('Unexpected query/species/invalid score was accepted')
    assert sf.sequence_parameters({'a':'malw*'},6183)['sequences']=='>a\nMALW'
    calls=[]
    def responder(method,params,timeout=45):
        calls.append((method,params))
        if method=='get_string_ids':raise sf.StringAPIError(404,method,{'http_status':404})
        return json.dumps(hits),{'method':'POST','url':sf.BASE+'/api/json/similarity_search'}
    with patch.object(sf,'api_request',side_effect=responder),patch.object(sf.time,'sleep') as sleep:
        result=sf.resolve_proteins(list(sequences),6183,sequences,'auto')
    assert [c[0] for c in calls]==['get_string_ids','similarity_search'] and sleep.call_count==1
    assert result['resolved']=={'a':'6183.A'} and result['status_by_query']['missing']=='Original sequence unavailable'
    assert len(result['sequence_hits'])==len(hits)
    assert sf.mapping_ids(result['raw'],list(sequences),6183)[0]==result['resolved']
    assert len(sf.tsv_rows(result['raw'],['queryItem','stringId']))==1
    # Successful ID mapping is retained; only unresolved inputs are sequenced.
    def partial(method,params,timeout=45):
        if method=='get_string_ids':return 'queryItem\tstringId\na\t6183.ID_A\n',{}
        assert '>a\n' not in params['sequences'] and '>b\n' in params['sequences']
        return json.dumps([hit('b','B')]),{}
    with patch.object(sf,'api_request',side_effect=partial),patch.object(sf.time,'sleep'):
        result=sf.resolve_proteins(['a','b'],6183,sequences,'auto')
    assert result['resolved']=={'a':'6183.ID_A','b':'6183.B'}
    # A service failure must not be disguised as unrecognized identifiers.
    with patch.object(sf,'api_request',side_effect=sf.StringAPIError(503,'get_string_ids',{})):
        try:sf.resolve_proteins(['a'],6183,sequences,'auto')
        except sf.StringAPIError as error:assert error.status==503
        else:raise AssertionError('Service error was suppressed')
    # The transport always POSTs sequences to the verified JSON endpoint.
    class Response:
        url=sf.BASE+'/api/json/similarity_search'
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):return b'[]'
    with patch.object(sf,'urlopen',return_value=Response()) as request:
        raw,log=sf.api_request('similarity_search',sf.sequence_parameters({'a':sequences['a']},6183))
        transport=request.call_args.args[0]
        assert transport.get_method()=='POST' and transport.full_url==Response.url and b'sequences=' in transport.data
    # All submitted proteins and hits survive sequential batching.
    progress=[]
    with patch.object(sf,'api_request',return_value=('[]',{})) as request,patch.object(sf.time,'sleep'):
        batch=sf.resolve_proteins([f'q{i}' for i in range(41)],6183,{f'q{i}':'MALW' for i in range(41)},'sequences',progress=progress.append)
    assert request.call_count==3 and len(batch['unresolved'])==41 and len(progress)==3
    print('PASS HTTP404 sequence fallback, identifier retention, species/query validation, ambiguity, missing sequences, all-hit evidence, POST transport and sequential batching',flush=True)
    if '--live' in sys.argv:live()


def live():
    root=Path(__file__).resolve().parents[1]
    ids=['Sman__Smp_079760','Sman__Smp_020540','Sman__Smp_014850'];sequences={}
    for path in (root/'family_specific_candidate_fasta').glob('*.faa'):
        current=None;parts=[]
        for line in path.read_text(encoding='utf-8-sig').splitlines()+['>END']:
            if line.startswith('>'):
                if current in ids:sequences[current]=''.join(parts)
                current=line[1:].split()[0];parts=[]
            else:parts.append(line.strip())
    assert len(sequences)==3
    result=sf.resolve_proteins(ids,6183,sequences,'sequences')
    assert result['resolved']['Sman__Smp_079760']=='6183.A0A3Q0KIA3'
    selected=[h for h in result['sequence_hits'] if h['decision']=='Selected sequence representative']
    assert next(h for h in selected if h['queryItem']==ids[0])['identity']==100
    from string_workbench import annotations_for_nodes,parse_network
    import pandas as pd
    candidates=pd.read_excel(root/'files/adhesome_candidates_list.xlsx',sheet_name='Audited_family_assignment')
    candidates['sequence_id']=candidates.protein_id;candidates['reviewed_family']=candidates.putative_audited_family_new
    candidates['orthogroup']=candidates.Orthology_Orthogroup;candidates['candidate_annotation']=candidates.protein_name
    plan=pd.DataFrame({'sequence_id':ids,'query_id':ids})
    nodes=annotations_for_nodes(result['resolved'].values(),candidates,pd.DataFrame(columns=['queryItem','stringId']),plan,result['resolved'],'Sman',6183)
    assert set(nodes.Family)-{'Unmapped'} and all(nodes.sequence_id)
    time.sleep(1);raw,network_log=sf.api_request('network',sf.network_parameters(sorted(set(result['resolved'].values())),6183))
    edges=parse_network(raw,6183)
    output=root/'.ui_review';output.mkdir(exist_ok=True)
    (output/'string_live_validation.json').write_text(json.dumps({'mapping':result,'network_request':network_log,'edges':len(edges)},indent=2),encoding='utf-8')
    print('PASS live STRING 12.5 original-sequence mapping:',result['resolved'],f'; {len(edges)} network edges; exact candidate-to-node joins',flush=True)


if __name__=='__main__':main()
