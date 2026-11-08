"""SMART query contracts, response polling and dossier integration (no live submissions)."""
from bootstrap import ATLAS_ROOT
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import pandas as pd
from smart_links import protein_url, architecture_url, parse_domains, identifier_options, query_manifest, sequence_form, is_protein_accession
from smart_fetch import fetch_query, validate_url, main as fetch_main, normalize_sequence, sequence_payload


def main():
    assert normalize_sequence('>protein\nac de\nFGH*\n') == 'ACDEFGH'
    assert sequence_payload('ACDE', False) == {'SEQUENCE': 'ACDE', 'TEXTONLY': '1'}
    form = sequence_form('ACDEFGH')
    assert 'method="post"' in form and 'name="SEQUENCE" value="ACDEFGH"' in form and 'TEXTONLY' not in form
    assert 'Open protein architecture in SMART' in form and 'name="ID"' not in form
    for accession in ['A0A3Q0KBZ0', 'Q8TEW0', 'P12345-2', 'ENSP00000312345.2', 'ENSMUSP00000123456']:
        assert is_protein_accession(accession), accession
    for gene in ['Smp_167010.1', 'MS3_00000278.1_mrna', 'EWB00_002919', 'Sman__Smp_006920', 'ENSG00000123456']:
        assert not is_protein_accession(gene), gene
        try:
            query_manifest(gene, [])
            raise AssertionError(gene)
        except ValueError:
            pass
    for bad in ['ACD-E', '>one\nACD\n>two\nEFG', 'AC*DE']:
        try:
            normalize_sequence(bad)
            raise AssertionError(bad)
        except ValueError:
            pass
    # Encoding prevents a pasted identifier from changing other GET parameters.
    url = protein_url('A0A3Q0KBZ0&GENOMIC=1', True)
    assert parse_qs(urlsplit(url).query) == {'ID': ['A0A3Q0KBZ0&GENOMIC=1'], 'TEXTONLY': ['1']}
    domains = parse_domains('SH3, SH3; SH2!TyrKc')
    assert domains == ['SH3', 'SH3', 'SH2', 'TyrKc']
    assert parse_qs(urlsplit(architecture_url(domains)).query)['identical'] == ['SH3!SH3!SH2!TyrKc!']
    assert 'similar=' in architecture_url(domains, False)
    rows = list(csv.DictReader(io.StringIO(query_manifest('Q8TEW0', domains))))
    assert len(rows) == 5  # protein + 3 distinct domain pages + repeated-domain architecture
    assert all(validate_url(row['url']) == row['url'] for row in rows)
    for bad in ['http://smart.embl.de/smart/show_motifs.pl?ID=x',
                'https://other.org/results.cgi?id=1', 'https://smart.embl.de:444/results.cgi?id=1',
                'https://smart.embl.de@other.org/results.cgi?id=1']:
        try:
            validate_url(bad)
            raise AssertionError(bad)
        except ValueError:
            pass
    # Candidate accession mapping must not pull a host orthologue from the same family.
    annotations = pd.DataFrame([
        {'sequence_id': 'Sman__Smp_006920', 'protein_annotation_id': 'A0A3Q0KBZ0', 'identifier_mapping_status': 'Mapped representative'},
        {'sequence_id': 'Hsap__TALIN', 'protein_annotation_id': 'Q9Y490', 'identifier_mapping_status': 'Mapped representative'}])
    records = pd.DataFrame([{'protein_id': 'Sman__Smp_006920'}])
    options = identifier_options('Sman__Smp_006920', records, annotations)
    assert options[0]['identifier'] == 'A0A3Q0KBZ0'
    assert 'Q9Y490' not in [row['identifier'] for row in options]
    assert 'Smp_006920' not in [row['identifier'] for row in options]
    assert identifier_options('Shae__MS3_00000278', pd.DataFrame([{'protein_id': 'MS3_00000278.1_mrna'}]), pd.DataFrame()) == []
    # Queue pages are not accepted as text results; poll the exact returned job URL.
    queued = 'https://smart.embl.de/results.cgi?id=123'
    responses = [(b'Job queued', queued, 'text/html'), (b'-- SMART RESULT\nSH2 10 80', queued, 'text/plain')]
    with patch('smart_fetch.get_response', side_effect=responses) as request, patch('smart_fetch.time.sleep'):
        result = fetch_query(None, protein_url('Q8TEW0', True))
        assert result[-1] == 'smart_text_result' and request.call_args.args[1] == queued
    with patch('smart_fetch.get_response', return_value=(b'Queued', queued, 'text/html')):
        assert fetch_query(None, protein_url('unknown', True), max_wait=0)[-1] == 'queue_timeout'
    with patch('smart_fetch.get_response', return_value=(b'<html>Unknown ID</html>', protein_url('unknown'), 'text/html')):
        assert fetch_query(None, protein_url('unknown'))[-1] == 'page_response'
    with patch('smart_fetch.get_response', return_value=(b'Queued', queued, 'text/html')):
        assert fetch_query(None, protein_url('unknown'))[-1] == 'queue_page'
    with patch('smart_fetch.get_response', side_effect=responses) as request, patch('smart_fetch.time.sleep'):
        result = fetch_query(None, 'https://smart.embl.de/smart/show_motifs.pl', post_data=sequence_payload('ACDE'))
        assert result[-1] == 'smart_text_result'
        assert parse_qs(request.call_args_list[0].args[3].decode())['SEQUENCE'] == ['ACDE']
    # Exercise the downloadable script's file/log/cache loop without network access.
    with tempfile.TemporaryDirectory(prefix='smart_test_', dir=Path(__file__).resolve().parents[1]) as folder:
        root = Path(folder)
        manifest = root / 'queries.csv'
        manifest.write_text(query_manifest('Q8TEW0', [], text_only=True), encoding='utf-8')
        args = ['smart_fetch.py', str(manifest), '--output', str(root / 'results'), '--fetch']
        with patch('sys.argv', args), patch('smart_fetch.get_response', return_value=(b'-- SMART RESULT\nPDZ', protein_url('Q8TEW0', True), 'text/plain')) as request:
            fetch_main()
            fetch_main()
            assert request.call_count == 1
        log = json.loads(next((root / 'results').glob('*.json')).read_text())
        assert log['status'] == 'smart_text_result' and log['query_url'] == protein_url('Q8TEW0', True)
        assert (root / 'results' / log['file']).read_bytes().startswith(b'-- SMART RESULT')
    print('PASS encoded GET URLs, repeated domains, candidate-only mapping, queue polling and page/result distinction', flush=True)


if __name__ == '__main__':
    main()
