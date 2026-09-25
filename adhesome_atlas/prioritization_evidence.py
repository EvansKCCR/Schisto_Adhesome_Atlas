from atlas_paths import phylogeny_root
"""Measured workbook and alignment features with explicit calculation bases."""
from pathlib import Path
import re
import pandas as pd


def alignment(path):
    result={}; key=None
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('>'):
            key=line[1:].split()[0]; result[key]=''
        elif key: result[key]+=line.strip().upper()
    return result


def enrich(frame, hits, root):
    out=frame.copy()
    ids=set(out.sequence_id)
    phylo={}; divergence={}; motif_scores={}
    by_id={k:g for k,g in hits.groupby('sequence_id')}
    for path in sorted((phylogeny_root(root)).rglob('trimmed.faa')):
        folder=path.parent.parent if path.parent.name=='inference' else path.parent
        if not path.exists(): continue
        seqs=alignment(path)
        present=ids & seqs.keys()
        if not present: continue
        branches=pd.read_csv(path.parent/'branch_evidence.tsv',sep='\t',dtype=str).fillna('')
        for key in present:
            seq=seqs[key]
            for host,other in seqs.items():
                if not host.startswith('Hsap__'): continue
                paired=[(a,b) for a,b in zip(seq,other) if a in 'ACDEFGHIKLMNPQRSTVWY' and b in 'ACDEFGHIKLMNPQRSTVWY']
                if paired:
                    score=sum(a!=b for a,b in paired)/len(paired)
                    divergence.setdefault(key,[]).append((score,f'{folder.relative_to(phylogeny_root(root)).as_posix()}: {host}; {len(paired)} paired amino-acid sites'))
            eligible=[]
            for row in branches.itertuples():
                tips=row.tip_ids.split(',')
                species={t.split('__')[0] for t in tips}
                if key in tips and species <= {'Shae','Sjap','Sman'} and len(species)>=2:
                    parts=row.support_label.split('/')
                    if len(parts)==2:
                        try: eligible.append((len(tips),min(float(x) for x in parts)/100,row.branch_id,row.support_label))
                        except ValueError: pass
            if eligible:
                smallest=min(x[0] for x in eligible)
                for _,score,branch,label in eligible:
                    if _==smallest: phylo.setdefault(key,[]).append((score,f'{folder.relative_to(phylogeny_root(root)).as_posix()}/{branch}: SH-aLRT/UFBoot {label}; smallest multispecies Schistosoma clade'))
            if key not in by_id: continue
            ungapped=''.join(a for a in seq if a not in '-.')
            columns=[i for i,a in enumerate(seq) if a not in '-.']
            for hit in by_id[key].itertuples():
                if getattr(hit,'role','encoded_motif') != 'encoded_motif': continue
                peptide=str(hit.peptide).upper()
                if not peptide or peptide=='NAN': continue
                starts=[m.start() for m in re.finditer('(?='+re.escape(peptide)+')',ungapped)]
                if len(starts)!=1: continue
                positions=columns[starts[0]:starts[0]+len(peptide)]
                other_species={k.split('__')[0] for k in seqs if k.startswith(('Shae__','Sjap__','Sman__')) and k.split('__')[0]!=key.split('__')[0]}
                scores=[]
                for species in other_species:
                    comparisons=[]
                    for k,other in seqs.items():
                        if k.startswith(species+'__'):
                            comparisons.append(sum(other[i]==a for i,a in zip(positions,peptide))/len(peptide))
                    if comparisons: scores.append(sum(comparisons)/len(comparisons))
                if scores:
                    motif_scores.setdefault((key,hit.family),[]).append((sum(scores)/len(scores),f'{folder.relative_to(phylogeny_root(root)).as_posix()}: {getattr(hit,'motif_label',getattr(hit,'elm_class','Motif'))}; uniquely retained peptide {peptide}; mean aligned residue identity across other Schistosoma species'))
    records=[]
    for _,r in out.iterrows():
        key=r.sequence_id
        h=by_id.get(key,pd.DataFrame())
        if len(h) and 'family' in h: h=h[h.family.eq(r.family)]
        context='; '.join(f'{getattr(x,'motif_label',getattr(x,'elm_class','Motif'))} {x.start}-{x.end}: {x.context_state}' for x in h.itertuples()) if len(h) else 'No motif hits recorded for this protein-family assignment'
        encoded=h[h.role.eq('encoded_motif')] if len(h) and 'role' in h else h
        states=set(encoded.context_state.dropna()) if len(encoded) else set()
        tiers='; '.join(f'{tier}: {count}' for tier,count in h.candidate_tier.value_counts().items()) if len(h) and 'candidate_tier' in h else ''

        motif='Region-supported motif' if 'region_supported' in states and not any('outside_expected' in str(s) for s in states) else 'Context conflict reported' if any('outside_expected' in str(s) for s in states) else 'Review-only motif annotation' if states=={'review_only'} else 'Sequence/window match only; context unresolved' if states else 'No contextual motif support reported'
        domain=pd.to_numeric(r.get('domain_type_fraction'),errors='coerce')
        copy_fraction=pd.to_numeric(r.get('domain_copy_fraction'),errors='coerce')
        if pd.notna(domain) and pd.notna(copy_fraction): domain=min(domain,copy_fraction)
        if pd.isna(domain):
            raw=str(r.get('domain_match','')).lower()
            domain=1.0 if raw in ('true','1','1.0') else 0.0 if raw in ('false','0','0.0') else float('nan')
        top=str(r.get('topology_evidence',''))
        topology=1.0 if top.startswith('Consistent') else 0.0 if 'discordance' in top else float('nan')
        audit_topology=pd.to_numeric(r.get('localization_score_0_1'),errors='coerce')
        if pd.notna(audit_topology): topology=float(audit_topology)
        record=dict(motif_context_evidence=motif,motif_hit_details=context,domain_architecture=domain,domain_architecture_basis='Minimum of workbook domain-type and domain-copy coverage where available; domain_match fallback',topology_compatibility=topology,topology_compatibility_basis='Workbook family-audit localization score' if pd.notna(audit_topology) else top)
        for field,values,reason in [('phylogenetic_support',phylo,'No supported multispecies Schistosoma clade with paired support labels'),('host_divergence',divergence,'No aligned human homologue with comparable amino-acid sites'),('motif_conservation',motif_scores,'No uniquely retained motif peptide with other Schistosoma species in trimmed alignment')]:
            entries=values.get((key,r.family) if field=='motif_conservation' else key,[])
            if entries:
                score,basis=min(entries,key=lambda x:x[0])
                record[field]=score; record[field+'_basis']=basis
            else: record[field]=float('nan');record[field+'_basis']=reason
        host=str(r.get('Orthology_Hsap_direct_orthologues',r.get('Hsap_orthologues','')))
        record['motif_assignment_tiers']=tiers or 'No candidate tiers recorded'
        record['motif_functional_assignment']=' | '.join(sorted(set(h.functional_hypothesis.dropna().astype(str)))) if len(h) and 'functional_hypothesis' in h else ''
        record['motif_context_evidence']=tiers if tiers else motif
        record['host_orthology_flag']='Human orthologues: '+host if host and host!='nan' else 'No human orthologue in source orthology results'
        record['priority_group']=r.get('priority_group','')
        if record['priority_group']=='Not in FN3 review collection': record['priority_group']='Adhesome / '+str(r.family)
        agree=bool(str(r.get('orthogroup',''))) and domain==1 and topology==1 and motif=='Region-supported motif'
        record['adhesome_interpretation']=('Convergent assignment: ' if agree else 'Integrated assignment: ')+str(r.get('assigned_family') if pd.notna(r.get('assigned_family')) else r.family)
        if 'audit_classification' in out:
            cls=r.audit_classification
            family=r.get('reviewed_family')
            label=str(family) if pd.notna(family) else str(r.family)
            record['adhesome_interpretation']=(
                f'{cls} family assignment: {label}' if cls in ('Supported','Provisional') else
                f'Ambiguous family assignment: {label}' if cls=='Ambiguous' else
                f'Family-level assignment not supported: {label}'
            )
        record['evidence_review_stage']=('1 · Orthology unresolved' if not str(r.get('orthogroup','')) else '2 · Architecture incomplete or mismatched' if pd.isna(domain) or domain<1 else '3 · Topology/localization incomplete or discordant' if pd.isna(topology) or topology<1 else '4 · Motif context incomplete or conflicting' if motif!='Region-supported motif' else '5 · Convergent integrated evidence')
        record['assignment_evidence_summary']=f"Orthology: {r.get('orthogroup','') or 'not recorded'}; domains: {r.get('domain_evidence','')}; topology: {top}; motifs: {motif}"
        records.append(record)
    derived=pd.DataFrame(records,index=out.index)
    for c in derived: out[c]=derived[c]
    return out
