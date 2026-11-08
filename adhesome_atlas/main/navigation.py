"""Stable destinations shared by candidate, research and classification links."""
from urllib.parse import urlencode,urlsplit,urlunsplit

HYPOTHESIS_PAGE='Interactive hypothesis'
PAGES=['Introduction',HYPOTHESIS_PAGE,'Components','Interactions','Orthology','Phylogeny',
    'Protein dossier','Motif explorer','Comments & feedback','Source Library','Citations']


def hypothesis_url(base,protein='',classification=''):
    parts=urlsplit(base or '')
    params={'view':HYPOTHESIS_PAGE}
    if protein:params['protein']=protein
    if classification:params['classification']=classification
    return urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(params),''))
