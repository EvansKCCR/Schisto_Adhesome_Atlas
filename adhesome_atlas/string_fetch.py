"""Reproducible STRING 12.5 mapping → network downloads, standard library only.

python3 string_fetch.py string_query.json --output STRING_results --fetch
Omit --fetch to preview. See https://string-db.org/help/api/.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = 'https://version-12-5.string-db.org'
CALLER = 'Schisto_Adhesome_Atlas'


class StringAPIError(ValueError):
    def __init__(self, status, method, log, detail=''):
        self.status, self.log = status, log
        super().__init__(f'STRING {method} returned HTTP {status}. '+detail)


def parameters(identifiers, species, **extra):
    values = list(dict.fromkeys(str(value).strip() for value in identifiers if str(value).strip()))
    if not values:
        raise ValueError('Choose at least one protein.')
    if not str(species).isdigit():
        raise ValueError('A numeric species taxon is required.')
    for value in values:
        if '\n' in value or '\r' in value:
            raise ValueError('Each protein identifier must occupy one line.')
    return {'identifiers': '\r'.join(values), 'species': str(species), 'caller_identity': CALLER, **extra}


def api_url(method, params, output='tsv'):
    if (method not in {'get_string_ids', 'network', 'similarity_search'} or
        output not in {'tsv', 'svg', 'highres_image', 'json'} or
        method=='similarity_search' and output!='json'):
        raise ValueError('Unsupported STRING endpoint.')
    params = dict(params)
    if output in {'svg', 'highres_image'} and 'add_nodes' in params:
        params['add_white_nodes'] = params.pop('add_nodes')
        params['add_color_nodes'] = 0
    return BASE + '/api/' + output + '/' + method + '?' + urlencode(params)


def api_request(method, params, timeout=45):
    url = api_url(method, params, 'json' if method=='similarity_search' else 'tsv')
    # Keep standardized GET queries for small lists; STRING recommends POST for long sets.
    data = None
    if method=='similarity_search' or len(url) > 1800:
        url = url.split('?')[0]
        data = urlencode(params).encode()
    request = Request(url, data=data, headers={'User-Agent': CALLER + '/1.0'})
    log={'method':'POST' if data else 'GET','url':url,'parameters':params,
         'retrieved_utc':datetime.now(timezone.utc).isoformat(),'string_version':'12.5'}
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(50_000_001)
            if len(body) > 50_000_000:
                raise ValueError('STRING response exceeds 50 MB; reduce the query or neighborhood.')
            return body.decode('utf-8-sig'), {'method': 'POST' if data else 'GET', 'url': url, 'parameters': params,
            'response_url': response.url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
            'sha256': hashlib.sha256(body).hexdigest(), 'string_version': '12.5'}
    except HTTPError as error:
        log.update(http_status=error.code,response_url=error.url)
        detail='No identifier matches may be available; try original protein sequences.' if method=='get_string_ids' and error.code==404 else 'Check species coverage and retry the request.'
        raise StringAPIError(error.code,method,log,detail) from error


def tsv_rows(text, required):
    if not text.strip():
        return []
    reader = csv.DictReader(io.StringIO(text), delimiter='\t')
    if not set(required) <= set(reader.fieldnames or []):
        raise ValueError('STRING did not return the expected TSV columns: ' + ', '.join(required))
    return list(reader)


def mapping_ids(text, identifiers, species):
    rows = tsv_rows(text, ['queryItem', 'stringId'])
    expected = set(identifiers)
    mapping = {}
    for row in rows:
        query = row['queryItem']
        if query not in expected:
            raise ValueError('STRING mapping contains an unexpected query identifier.')
        if not row['stringId'].startswith(str(species) + '.'):
            raise ValueError('STRING mapping returned a different species.')
        mapping.setdefault(query, set()).add(row['stringId'])
    resolved = {query: next(iter(ids)) for query, ids in mapping.items() if len(ids) == 1}
    return resolved, sorted(expected - set(resolved))


def normalize_sequence(sequence):
    sequence=re.sub(r'\s+','',str(sequence)).upper().rstrip('*')
    if not sequence or not re.fullmatch(r'[ACDEFGHIKLMNPQRSTVWYBXZJUO]+',sequence):
        raise ValueError('Expected an original amino-acid sequence without gaps or internal stop codons.')
    return sequence


def sequence_parameters(sequences,species):
    """Use the similarity_search endpoint used by STRING's official server.

    Reference: https://github.com/meringlab/string-mcp/blob/master/server.py
    Sequence identity is a local alignment statistic, not full-length coverage.
    """
    parameters(list(sequences),species)  # validate taxon and nonempty query IDs
    records=[]
    for identifier,sequence in sequences.items():
        if not re.fullmatch(r'[A-Za-z0-9_.:|+-]+',identifier):
            raise ValueError('Sequence query headers must be single, whitespace-free protein identifiers.')
        records.append('>'+identifier+'\n'+normalize_sequence(sequence))
    return {'sequences':'\n'.join(records),'species':str(species),'caller_identity':CALLER}


def sequence_matches(text,identifiers,species,min_identity=80,max_evalue=1e-5,min_score_gap=.05):
    hits=json.loads(text)
    if not isinstance(hits,list):
        raise ValueError('STRING sequence search did not return an alignment list.')
    expected=set(identifiers);by_query={query:[] for query in identifiers};rows=[]
    for original in hits:
        if not isinstance(original,dict) or not {'querySequenceName','hitStringId','identity','E-value','bitscore'}<=set(original):
            raise ValueError('Unexpected STRING sequence alignment fields.')
        row=dict(original);query=row['querySequenceName'];sid=row['hitStringId']
        if query not in expected or not sid.startswith(str(species)+'.') or str(row.get('hitNcbiTaxonId',species))!=str(species):
            raise ValueError('STRING sequence search returned an unexpected query or species.')
        identity,evalue,score=float(row['identity']),float(row['E-value']),float(row['bitscore'])
        if not 0<=identity<=100 or not 0<=evalue<float('inf') or not 0<score<float('inf'):
            raise ValueError('Invalid identity, E-value or alignment bitscore returned by STRING.')
        row.update(queryItem=query,stringId=sid,mapping_source='Protein sequence similarity',decision='Below mapping thresholds')
        rows.append(row);by_query[query].append(row)
    resolved={};states={}
    for query,query_hits in by_query.items():
        eligible=[r for r in query_hits if float(r['identity'])>=min_identity and float(r['E-value'])<=max_evalue]
        # Deduplicate a representative ID before evaluating ambiguity.
        representatives={}
        for hit in eligible:
            if hit['stringId'] not in representatives or float(hit['bitscore'])>float(representatives[hit['stringId']]['bitscore']):representatives[hit['stringId']]=hit
        ranked=sorted(representatives.values(),key=lambda r:(-float(r['bitscore']),r['stringId']))
        if not ranked:states[query]='No sequence hits' if not query_hits else 'No sequence hit passes mapping thresholds';continue
        best=ranked[0];gap=(float(best['bitscore'])-float(ranked[1]['bitscore']))/float(best['bitscore']) if len(ranked)>1 else 1
        for hit in eligible:hit['decision']='Alternative sequence hit'
        if len(ranked)>1 and (gap<min_score_gap or float(best['bitscore'])==float(ranked[1]['bitscore'])):
            states[query]='Ambiguous sequence representatives'
            for hit in ranked:hit['decision']='Ambiguous sequence representative'
        else:
            resolved[query]=best['stringId'];states[query]='Sequence representative mapped';best['decision']='Selected sequence representative'
    return resolved,states,rows


def mapping_tsv(rows):
    fields=['queryItem','stringId','ncbiTaxonId','preferredName','mapping_source','identity','E-value','bitscore']
    output=io.StringIO();writer=csv.DictWriter(output,fields,delimiter='\t',lineterminator='\n',extrasaction='ignore');writer.writeheader();writer.writerows(rows);return output.getvalue()


def resolve_proteins(identifiers,species,sequences=None,mode='auto',min_identity=80,max_evalue=1e-5,min_score_gap=.05,progress=None):
    """Resolve IDs and/or original sequences, retaining every alignment hit."""
    identifiers=list(dict.fromkeys(identifiers));parameters(identifiers,species)
    if mode not in {'auto','sequences','identifiers'}:raise ValueError('Unknown STRING mapping mode.')
    if not 0<=min_identity<=100 or not 0<max_evalue<float('inf') or not 0<=min_score_gap<=1:raise ValueError('Invalid sequence-mapping thresholds.')
    sequences=sequences or {};resolved={};states={};selected=[];all_hits=[];identifier_raw=''
    log={'mode':mode,'string_version':'12.5','species':str(species),'sequence_requests':[],
         'sequence_thresholds':{'min_identity_percent':min_identity,'max_evalue':max_evalue,'min_relative_bitscore_gap':min_score_gap}}
    had_request=False
    if mode!='sequences':
        try:
            identifier_raw,request_log=api_request('get_string_ids',parameters(identifiers,species,echo_query=1));resolved,_=mapping_ids(identifier_raw,identifiers,species)
            log['identifier_request']=request_log
            for row in tsv_rows(identifier_raw,['queryItem','stringId']):
                if resolved.get(row['queryItem'])==row['stringId']:selected.append({**row,'mapping_source':'Protein identifier'})
        except StringAPIError as error:
            if error.status!=404:raise
            log['identifier_request']=error.log
        had_request=True
    for query in identifiers:states[query]='Identifier mapped' if query in resolved else 'Identifier unresolved'
    pending=[q for q in identifiers if q not in resolved]
    if mode!='identifiers':
        available={q:normalize_sequence(sequences[q]) for q in pending if sequences.get(q)}
        for query in pending:
            if query not in available:states[query]='Original sequence unavailable'
        log['sequence_inputs']={q:{'length':len(s),'sha256':hashlib.sha256(s.encode()).hexdigest()} for q,s in available.items()}
        batches=[];batch={};residues=0
        for query,sequence in available.items():
            if batch and (len(batch)>=20 or residues+len(sequence)>100000):batches.append(batch);batch={};residues=0
            batch[query]=sequence;residues+=len(sequence)
        if batch:batches.append(batch)
        for index,batch in enumerate(batches):
            if had_request:time.sleep(1)
            if progress:progress(f'Sequence batch {index+1} of {len(batches)} · {len(batch)} proteins')
            text,request_log=api_request('similarity_search',sequence_parameters(batch,species),timeout=120);had_request=True
            mapping,batch_states,hits=sequence_matches(text,list(batch),species,min_identity,max_evalue,min_score_gap)
            resolved.update(mapping);states.update(batch_states);all_hits.extend(hits);log['sequence_requests'].append(request_log)
            for hit in hits:
                if hit['decision']=='Selected sequence representative':selected.append({'queryItem':hit['queryItem'],'stringId':hit['stringId'],'ncbiTaxonId':str(species),'preferredName':hit.get('hitPreferredName',''),**{k:hit[k] for k in ['mapping_source','identity','E-value','bitscore']}})
    return {'raw':mapping_tsv(selected),'resolved':resolved,'unresolved':[q for q in identifiers if q not in resolved],
            'status_by_query':states,'sequence_hits':all_hits,'identifier_raw':identifier_raw,'log':log}


def network_parameters(identifiers, species, score=400, add_nodes=0, network_type='functional'):
    if network_type not in {'functional', 'physical'}:
        raise ValueError('Use functional or physical networks for undirected topology.')
    if not 0 <= int(score) <= 1000 or not 0 <= int(add_nodes) <= 100:
        raise ValueError('Score must be 0–1000 and additional nodes 0–100.')
    return parameters(identifiers, species, required_score=int(score), add_nodes=int(add_nodes), network_type=network_type)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('--output', type=Path, default=Path('STRING_results'))
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    identifiers = config['identifiers']
    species = config['species']
    map_params = parameters(identifiers, species, echo_query=1)
    options = {key: config.get(key, default) for key, default in [('score', 400), ('add_nodes', 0), ('network_type', 'functional')]}
    network_parameters(identifiers, species, **options)
    if config.get('mapping_mode','auto')!='sequences':print(api_url('get_string_ids', map_params))
    if config.get('mapping_mode','auto')!='identifiers':print('POST '+BASE+'/api/json/similarity_search (original protein FASTA)')
    if not args.fetch:
        print('Preview only. Add --fetch to resolve identifiers and download the network.')
        return
    args.output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    prefix = 'string_' + str(species) + '_' + stamp
    result=resolve_proteins(identifiers,species,config.get('sequences'),config.get('mapping_mode','auto'),**config.get('sequence_thresholds',{}))
    mapping_text=result['raw'];mapped=result['resolved'];unresolved=result['unresolved']
    (args.output / (prefix + '_mapping.tsv')).write_text(mapping_text, encoding='utf-8')
    (args.output/(prefix+'_sequence_hits.json')).write_text(json.dumps(result['sequence_hits'],indent=2)+'\n',encoding='utf-8')
    log = {'config': config, 'mapping_request': result['log'], 'resolved': mapped, 'unresolved': unresolved,'status_by_query':result['status_by_query']}
    log_path = args.output / (prefix + '_run.json')
    log_path.write_text(json.dumps(log, indent=2) + '\n', encoding='utf-8')
    if not mapped:
        raise SystemExit('No protein identifiers were resolved. Check the mapping file.')
    time.sleep(1)
    params = network_parameters(sorted(set(mapped.values())), species, **options)
    network_text, network_log = api_request('network', params)
    tsv_rows(network_text, ['stringId_A', 'stringId_B', 'score'])
    path = args.output / (prefix + '_network.tsv')
    path.write_text(network_text, encoding='utf-8')
    log['network_request'] = network_log
    log_path.write_text(json.dumps(log, indent=2) + '\n', encoding='utf-8')
    print('Network: ' + str(path))
    print('Unresolved identifiers: ' + str(len(unresolved)))
    print('Upload the network and mapping TSVs in Interactions > STRING query & import.')


if __name__ == '__main__':
    main()
