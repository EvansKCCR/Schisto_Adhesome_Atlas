from pathlib import Path

def phylogeny_root(root):
    matches=[p for p in Path(root).iterdir() if p.is_dir() and p.name.casefold()=='phylogeny']
    if len(matches)>1: raise ValueError('Both Phylogeny and phylogeny exist; keep one data directory.')
    return matches[0] if matches else Path(root)/'Phylogeny'
