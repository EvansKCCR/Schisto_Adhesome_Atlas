"""SMART GET downloads and original-sequence POST analysis; standard library only.

Preview: python3 smart_fetch.py smart_queries.csv --output SMART_results
Fetch:   python3 smart_fetch.py smart_queries.csv --output SMART_results --fetch
Sequence: python3 smart_fetch.py --fasta protein.fasta --output SMART_results --fetch
Reference: https://smart.embl.de/faq.cgi
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import parse_qs, urlsplit, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

PATHS = {'/smart/show_motifs.pl', '/smart/do_annotation.pl',
         '/smart/show_identical.cgi', '/results.cgi', '/smart/results.cgi'}


def validate_url(url):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.hostname != 'smart.embl.de' or
            parts.username or parts.password or parts.port not in (None, 443) or
            parts.path not in PATHS):
        raise ValueError('Expected an HTTPS SMART query URL: ' + url)
    return url


class SmartRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(request, response, code, message, headers, newurl)


def get_response(opener, url, timeout, data=None):
    validate_url(url)
    with opener.open(Request(url, data=data, headers={'User-Agent': 'Schisto-Adhesome-Atlas-SMART/1.0'}), timeout=timeout) as response:
        validate_url(response.url)
        return response.read(), response.url, response.headers.get('Content-Type', '')


def fetch_query(opener, url, timeout=60, poll_interval=10, max_wait=600, post_data=None):
    if post_data is None:
        data, final_url, content_type = get_response(opener, url, timeout)
    else:
        data, final_url, content_type = get_response(opener, url, timeout, urlencode(post_data).encode())
    deadline = time.monotonic() + max_wait
    job_url = urlsplit(final_url)
    queued = job_url.path in {'/results.cgi', '/smart/results.cgi'} and bool(parse_qs(job_url.query).get('id'))
    text_only = str((post_data or {}).get('TEXTONLY', '')) == '1' or parse_qs(urlsplit(url).query).get('TEXTONLY') == ['1']
    if queued and not text_only:
        return data, final_url, content_type, 'queue_page'
    while queued and b'-- SMART RESULT' not in data:
        if time.monotonic() + poll_interval > deadline:
            return data, final_url, content_type, 'queue_timeout'
        time.sleep(poll_interval)
        data, final_url, content_type = get_response(opener, final_url, timeout)
    status = 'smart_text_result' if b'-- SMART RESULT' in data else 'page_response'
    return data, final_url, content_type, status


def normalize_sequence(value):
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if sum(line.startswith('>') for line in lines) > 1:
        raise ValueError('Submit one protein at a time.')
    sequence = ''.join(line for line in lines if not line.startswith('>')).replace(' ', '').replace('\t', '').upper()
    sequence = sequence.rstrip('*')
    if not sequence or not re.fullmatch(r'[ACDEFGHIKLMNPQRSTVWYBXZJUO]+', sequence):
        raise ValueError('Enter an amino-acid sequence or single-record protein FASTA (no gaps or internal stops).')
    return sequence


def sequence_payload(sequence, pfam=True):
    payload = {'SEQUENCE': normalize_sequence(sequence), 'TEXTONLY': '1'}
    if pfam:
        payload['DO_PFAM'] = '1'
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path, nargs='?')
    parser.add_argument('--fasta', type=Path, help='Submit one original protein sequence by POST instead of GET queries.')
    parser.add_argument('--no-pfam', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('SMART_results'))
    parser.add_argument('--fetch', action='store_true', help='Execute requests; otherwise preview only.')
    parser.add_argument('--delay', type=float, default=5, help='Seconds between queries; minimum 5.')
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--max-wait', type=float, default=600, help='Maximum polling duration per queued result.')
    args = parser.parse_args()
    if args.delay < 5 or args.timeout <= 0 or args.max_wait < 0:
        parser.error('delay must be >= 5, timeout > 0, and max-wait >= 0')
    if bool(args.manifest) == bool(args.fasta):
        parser.error('Provide either a GET query CSV or --fasta, not both.')
    if args.fasta:
        payload = sequence_payload(args.fasta.read_text(encoding='utf-8-sig'), not args.no_pfam)
        rows = [{'label': args.fasta.stem, 'url': 'https://smart.embl.de/smart/show_motifs.pl', 'post_data': payload}]
    else:
        with args.manifest.open(encoding='utf-8-sig', newline='') as source:
            reader = csv.DictReader(source)
            if not {'label', 'url'} <= set(reader.fieldnames or []):
                parser.error('CSV must have label and url columns.')
            rows = list(reader)
    for row in rows:
        validate_url(row['url'])
    if not args.fetch:
        for row in rows:
            print(row['label'] + '\t' + row['url'] + ('\tPOST SEQUENCE (' + str(len(row['post_data']['SEQUENCE'])) + ' aa)' if 'post_data' in row else ''))
        print('Preview only. Add --fetch to download.')
        return
    args.output.mkdir(parents=True, exist_ok=True)
    opener = build_opener(SmartRedirect())
    requested = False
    failed = False
    for row in rows:
        url = row['url']
        # A query digest prevents collisions when accession, options or architecture change.
        stem = re.sub(r'[^A-Za-z0-9_.-]+', '_', row['label']).strip('._')[:70] or 'query'
        request_digest = hashlib.sha256((url + (json.dumps(row['post_data'], sort_keys=True) if 'post_data' in row else '')).encode()).hexdigest()
        stem += '_' + request_digest[:12]
        log_path = args.output / (stem + '.json')
        if log_path.exists():
            log = json.loads(log_path.read_text(encoding='utf-8'))
            previous = args.output / Path(log.get('file', '')).name
            if log.get('status') in {'page_response', 'smart_text_result'} and previous.is_file() and previous.stat().st_size:
                print('Cached: ' + row['label'])
                continue
        if requested:
            time.sleep(args.delay)
        requested = True
        log = {'label': row['label'], 'query_url': url, 'method': 'POST' if 'post_data' in row else 'GET', 'request_sha256': request_digest}
        if 'post_data' in row:
            log.update(sequence_sha256=hashlib.sha256(row['post_data']['SEQUENCE'].encode()).hexdigest(),
                       sequence_length=len(row['post_data']['SEQUENCE']), include_pfam='DO_PFAM' in row['post_data'])
        try:
            data, final_url, content_type, status = fetch_query(opener, url, args.timeout, max_wait=args.max_wait, post_data=row.get('post_data'))
            extension = '.txt' if status == 'smart_text_result' or 'text/plain' in content_type else '.html'
            target = args.output / (stem + extension)
            target.write_bytes(data)
            log.update(status=status, response_url=final_url, content_type=content_type, file=target.name)
            print(status + ': ' + str(target))
            failed |= status == 'queue_timeout'
        except Exception as error:
            log.update(status='error', error=str(error))
            failed = True
            print('Error: ' + row['label'] + ': ' + str(error))
        log_path.write_text(json.dumps(log, indent=2) + '\n', encoding='utf-8')
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
