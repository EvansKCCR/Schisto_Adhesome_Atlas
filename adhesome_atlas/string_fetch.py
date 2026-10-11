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
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = 'https://version-12-5.string-db.org'
CALLER = 'Schisto_Adhesome_Atlas'


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
    if method not in {'get_string_ids', 'network'} or output not in {'tsv', 'svg', 'highres_image'}:
        raise ValueError('Unsupported STRING endpoint.')
    params = dict(params)
    if output in {'svg', 'highres_image'} and 'add_nodes' in params:
        params['add_white_nodes'] = params.pop('add_nodes')
        params['add_color_nodes'] = 0
    return BASE + '/api/' + output + '/' + method + '?' + urlencode(params)


def api_request(method, params, timeout=45):
    url = api_url(method, params)
    # Keep standardized GET queries for small lists; STRING recommends POST for long sets.
    data = None
    if len(url) > 1800:
        url = url.split('?')[0]
        data = urlencode(params).encode()
    request = Request(url, data=data, headers={'User-Agent': CALLER + '/1.0'})
    with urlopen(request, timeout=timeout) as response:
        body = response.read(50_000_001)
        if len(body) > 50_000_000:
            raise ValueError('STRING response exceeds 50 MB; reduce the query or neighborhood.')
        return body.decode('utf-8-sig'), {'method': 'POST' if data else 'GET', 'url': url, 'parameters': params,
            'response_url': response.url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
            'sha256': hashlib.sha256(body).hexdigest(), 'string_version': '12.5'}


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
    print(api_url('get_string_ids', map_params))
    if not args.fetch:
        print('Preview only. Add --fetch to resolve identifiers and download the network.')
        return
    args.output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    prefix = 'string_' + str(species) + '_' + stamp
    mapping_text, mapping_log = api_request('get_string_ids', map_params)
    mapped, unresolved = mapping_ids(mapping_text, identifiers, species)
    (args.output / (prefix + '_mapping.tsv')).write_text(mapping_text, encoding='utf-8')
    log = {'config': config, 'mapping_request': mapping_log, 'resolved': mapped, 'unresolved': unresolved}
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
