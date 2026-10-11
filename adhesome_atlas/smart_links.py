"""SMART sequence submission and optional accession/domain queries."""
import csv
import io
import re
from pathlib import Path
from urllib.parse import urlencode

BASE = 'https://smart.embl.de'
FAQ = BASE + '/faq.cgi'


def is_protein_accession(identifier):
    """Accept UniProt accessions or Ensembl protein IDs, excluding local gene IDs."""
    return bool(re.fullmatch(
        r'(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})(?:-\d+)?'
        r'|ENS[A-Z]*P[0-9]+(?:\.[0-9]+)?', identifier.strip()))


def protein_url(identifier, text_only=False):
    params = {'ID': identifier.strip()}
    if not params['ID']:
        raise ValueError('Enter a protein identifier.')
    if text_only:
        params['TEXTONLY'] = '1'
    return BASE + '/smart/show_motifs.pl?' + urlencode(params)


def domain_url(domain):
    domain = domain.strip()
    if not re.fullmatch(r'[A-Za-z0-9_.:-]+', domain):
        raise ValueError('Use one SMART domain name or accession, such as SH2.')
    return BASE + '/smart/do_annotation.pl?' + urlencode({'DOMAIN': domain})


def architecture_url(domains, ordered=True):
    """Use the current protein page's organisation/composition query format."""
    if not domains:
        raise ValueError('Enter at least one SMART domain name.')
    for domain in domains:
        domain_url(domain)
    parameter = 'identical' if ordered else 'similar'
    return BASE + '/smart/show_identical.cgi?' + urlencode({parameter: '!'.join(domains) + '!'})


def parse_domains(value):
    domains = [name for name in re.split(r'[\s,;!]+', value.strip()) if name]
    for domain in domains:
        domain_url(domain)
    return domains


def identifier_options(key, records, annotations):
    """Keep accession suggestions tied to this candidate, never its host orthologue."""
    from identifier_labels import canonical_sequence_id
    canonical = canonical_sequence_id(key)
    protein = canonical.split('__')[-1]
    options = []

    def add(value, basis):
        if value is None or str(value).strip().lower() in ('', 'nan', 'none', '<na>'):
            return
        for token in re.split(r'\s*[|;]\s*', str(value)):
            token = token.split('__')[-1].strip()
            if token and not any(item['identifier'] == token for item in options):
                options.append({'identifier': token, 'basis': basis})

    if not annotations.empty:
        matches = annotations[annotations.sequence_id.eq(canonical) |
                              annotations.protein_annotation_id.eq(protein)]
        for row in matches.to_dict('records'):
            if row.get('identifier_mapping_status') == 'Mapped representative':
                add(row.get('protein_annotation_id'), 'Identifier map · representative protein')
    for column in ['protein_annotation_id', 'uniprot_accession', 'UniProt_accession', 'accession', 'protein_id']:
        if column in records:
            for value in records[column]:
                add(value, 'Candidate annotation · ' + column)
    add(protein, 'Atlas sequence identifier')
    # Gene IDs and local transcript/protein labels cannot identify SMART records.
    return [item for item in options if is_protein_accession(item['identifier'])]


def query_manifest(identifier, domains, ordered=True, text_only=False):
    rows = []
    if identifier.strip():
        if not is_protein_accession(identifier):
            raise ValueError('Use a UniProt accession or Ensembl protein ID for an accession query.')
        rows.append({'label': 'protein_' + identifier.strip(), 'url': protein_url(identifier, text_only)})
    rows.extend({'label': 'domain_' + name, 'url': domain_url(name)} for name in dict.fromkeys(domains))
    if domains:
        rows.append({'label': 'architecture_' + ('ordered' if ordered else 'composition'),
                     'url': architecture_url(domains, ordered)})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['label', 'url'])
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def sequence_form(sequence, pfam=True):
    """Browser POST avoids putting long protein sequences into a GET URL."""
    from html import escape
    from smart_fetch import sequence_payload
    payload = sequence_payload(sequence, pfam)
    payload.pop('TEXTONLY')  # Browser opens SMART's graphical results rather than text output.
    fields = ''.join('<input type="hidden" name="' + name + '" value="' + escape(value, quote=True) + '">' for name, value in payload.items())
    return '<form action="' + BASE + '/smart/show_motifs.pl" method="post" target="_blank">' + fields + '<button type="submit" style="background:#064c2c;color:white;border:0;border-bottom:4px solid #f4cf24;border-radius:8px;padding:12px 18px;font:bold 16px Arial;cursor:pointer">Open protein architecture in SMART ↗</button></form>'


def smart_panel(key, records, sequence=''):
    import streamlit as st
    from identifier_labels import identifier_annotations
    st.markdown('### SMART domain architecture lookup')
    st.write('Query SMART with the original protein sequence to display its domain architecture. Explore domain descriptions and proteins sharing a domain organisation or composition below.')
    options = identifier_options(key, records, identifier_annotations())
    prefix = 'smart_' + key
    with st.expander('Original protein sequence → SMART architecture', expanded=True):
        from smart_fetch import normalize_sequence
        value = st.text_area('Protein sequence / FASTA', value=sequence, height=125, key=prefix + '_sequence')
        pfam = st.checkbox('Include Pfam in SMART sequence analysis', value=True, key=prefix + '_pfam')
        try:
            normalized = normalize_sequence(value)
        except ValueError as error:
            st.info(str(error))
        else:
            st.caption(f'{len(normalized):,} amino acids · Open protein architecture in SMART submits this sequence directly. SMART displays existing results for recognized sequences or queues a new analysis.')
            st.iframe(sequence_form(normalized, pfam), height=65)
            fasta_name = re.sub(r'[^A-Za-z0-9_.-]', '_', key) + '_SMART.fasta'
            st.download_button('Download sequence for SMART', '>' + key + '\n' + normalized + '\n', fasta_name, 'text/plain', key=prefix + '_seq_fasta')
            script = Path(__file__).with_name('smart_fetch.py')
            st.download_button('Download SMART sequence script', script.read_bytes(), script.name, 'text/x-python', key=prefix + '_seq_script')
            st.code('python3 smart_fetch.py --fasta ' + fasta_name + ' --output SMART_results --fetch' + (' --no-pfam' if not pfam else ''), language='bash')
            st.caption('The WSL script submits SEQUENCE by POST with TEXTONLY=1, waits for queued results, and saves the response plus sequence-hash provenance. The browser button opens graphical SMART results in a new tab.')
    left, right = st.columns([1.1, 1])
    with left:
        with st.expander('Optional UniProt / Ensembl protein accession lookup'):
            selected = ''
            if options:
                selected = st.selectbox('Candidate protein accession', [item['identifier'] for item in options], key=prefix + '_accession_choice')
                st.caption(next(item['basis'] for item in options if item['identifier'] == selected))
            identifier = st.text_input('UniProt accession / Ensembl protein ID', value=selected, placeholder='e.g. A0A3Q0KBZ0', key=prefix + '_accession_' + selected).strip()
            text_only = st.checkbox('Plain-text response (TEXTONLY=1)', key=prefix + '_text')
            if identifier and not is_protein_accession(identifier):
                st.error('Enter a UniProt accession or Ensembl protein ID. For local gene IDs, use the original sequence button above.')
                identifier = ''
            if identifier:
                st.link_button('Look up protein accession in SMART', protein_url(identifier, text_only), width='stretch')
            st.caption('Only protein accession formats are offered here; record availability is determined by SMART. The main architecture button uses the sequence and requires no accession.')
    with right:
        value = st.text_input('SMART domain names in N → C order', placeholder='SH3, SH2, TyrKc', key=prefix + '_domains')
        mode = st.radio('Architecture matching', ['Domain organisation (ordered)', 'Domain composition'], key=prefix + '_mode')
        domains = []
        try:
            domains = parse_domains(value)
        except ValueError as error:
            st.error(str(error))
        if domains:
            st.link_button('Find matching domain architectures', architecture_url(domains, mode.startswith('Domain organisation')), width='stretch')
            for name in dict.fromkeys(domains):
                st.link_button('Domain page · ' + name, domain_url(name))
        st.caption('Use SMART names, retaining repeated domains. Organisation preserves their order and permits extra domains; composition requires the query domain types. Pfam/CDD labels in the atlas are not automatically translated to SMART names.')
        st.markdown('[Browse SMART domain names and descriptions](' + BASE + '/domains.cgi)')
    with st.expander('Standardized URL queries and WSL download script'):
        st.write('The Atlas builds URL-encoded GET links locally. Opening a link contacts SMART; browsing this dossier makes no SMART request.')
        st.code('show_motifs.pl?ID=<protein>\nshow_motifs.pl?ID=<protein>&TEXTONLY=1\ndo_annotation.pl?DOMAIN=<domain>\nshow_identical.cgi?identical=<domain1>!<domain2>!\nshow_identical.cgi?similar=<domain1>!<domain2>!', language='text')
        st.write('Download the query CSV and script into the same WSL directory. The script retrieves pages sequentially, skips existing results, logs response URLs, and waits for queued text results.')
        st.download_button('Download SMART query CSV', query_manifest(identifier, domains, mode.startswith('Domain organisation'), text_only),
                           'smart_queries.csv', 'text/csv', key=prefix + '_csv')
        script = Path(__file__).with_name('smart_fetch.py')
        st.download_button('Download SMART GET script', script.read_bytes(), script.name, 'text/x-python', key=prefix + '_script')
        st.code('python3 smart_fetch.py smart_queries.csv --output SMART_results\npython3 smart_fetch.py smart_queries.csv --output SMART_results --fetch', language='bash')
        st.caption('The first command previews the requests; --fetch downloads responses with a five-second minimum interval. HTML is a page response, not a self-contained architecture figure. Use SMART’s viewer to export its diagram as SVG or bitmap; there is no documented static figure-download URL used here.')
        st.markdown('[SMART FAQ and official sequence-submission script](' + FAQ + ') · [SMART protein example](' + protein_url('Q8TEW0') + ')')
        st.write('Use Open protein architecture in SMART above to submit the original sequence. The same script supports --fasta for SMART’s POST-and-poll sequence workflow.')
