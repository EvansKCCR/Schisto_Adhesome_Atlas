"""Transparent review hierarchy; never promote orthology to adhesion membership."""
import re
import pandas as pd

PRIORITIES = ['Schistosoma-only single-pass FN3 receptors', 'Schistosoma-only RPTP-like proteins', 'Conserved secreted FN3 proteins']

def value(row, *names):
    for name in names:
        v = row.get(name)
        if v is not None and pd.notna(v) and str(v).strip():
            return str(v).strip()
    return ''

def annotate(frame):
    frame = frame.copy()
    derived=[]
    for _,r in frame.iterrows():
        group=value(r,'Orthology_Orthogroup','Orthogroup')
        state=value(r,'Orthology_HOG_status','HOG_status')
        mapping=value(r,'Orthology_mapping_status','orthology_mapping_status')
        orth=bool(group and mapping=='matched')
        family=value(r,'assigned_family','family')
        arch=value(r,'architecture','Pfam_architecture')
        tm=value(r,'DeepTMHMM'); loc=value(r,'DeepLoc_2.1')
        context=value(r,'MotifScan_context_state','motif_scan_context')
        counts=[pd.to_numeric(value(r,'Orthology_'+s+'_HOG_copy_count',s+'_HOG_copy_counts'),errors='coerce') for s in ['Shae','Sjap','Sman']]
        species_count=sum(x>0 for x in counts) if all(pd.notna(x) for x in counts) else None
        domain='Unassessed'
        if value(r,'domain_match').lower() in ['true','1','1.0']:
            domain='Family rule matched; diagnostic specificity requires review'
        elif value(r,'domain_match').lower() in ['false','0','0.0']:
            domain='Family rule mismatch'
        elif 'FN3' in family or 'phosphatase' in family:
            if 'PF00041:' in arch:
                domain='FN3 detected; not diagnostic of adhesion'
                if family=='receptor_protein_tyrosine_phosphatase_like':
                    domain='FN3 + phosphatase architecture' if 'PF00102:' in arch else 'RPTP assignment needs architecture review'
        topology='Unassessed'
        module=value(r,'module')
        if loc and tm:
            if family=='secreted_FN3_protein_like':
                topology='Consistent with secreted assignment' if tm.startswith('SP') and not re.search(r'\bTM\b',tm) and 'Extracellular' in loc else 'Secreted assignment: topology/localization discordance'
            elif family in ['single_pass_FN3_adhesion_receptor_like','receptor_protein_tyrosine_phosphatase_like'] or module=='integrin_receptors':
                segments=re.findall(r'\bTM\s+(\d+-\d+(?:,\d+-\d+)*)',tm)
                n=sum(len(s.split(',')) for s in segments)
                topology='Consistent with membrane assignment' if n==1 and 'Cell membrane' in loc else 'Membrane assignment needs topology/localization review'
            elif module=='extracellular_matrix':
                topology='Consistent with extracellular assignment' if 'Extracellular' in loc and tm.startswith('SP') else 'Extracellular assignment needs topology/localization review'
            elif module in ['actin_linking','membrane_proximal_adaptors','focal_adhesion_scaffolds','downstream_signalling']:
                topology='Consistent with intracellular/peripheral assignment' if ('Cytoplasm' in loc or 'Cell membrane' in loc) and 'GLOB' in tm else 'Intracellular assignment needs topology/localization review'
        if 'outside_expected' in context: motif='Context conflict reported'
        elif 'region_supported' in context: motif='Region-supported candidate; binding unvalidated'
        elif context: motif='Sequence/window match only; context unresolved'
        else: motif='No contextual motif support reported'
        priority='Other / unresolved FN3 candidates'
        if state=='Schistosoma-only in sampled HOG' and family=='single_pass_FN3_adhesion_receptor_like':priority=PRIORITIES[0]
        elif state=='Schistosoma-only in sampled HOG' and family=='receptor_protein_tyrosine_phosphatase_like':priority=PRIORITIES[1]
        elif state=='shared HOG' and family=='secreted_FN3_protein_like' and species_count==3:priority=PRIORITIES[2]
        if 'fibronectin_like' not in value(r,'family'):priority='Not in FN3 review collection'
        # These are review stages, never positive membership classifications.
        if not orth:stage='1 · Orthology unresolved; retain candidate'
        elif domain in ['Unassessed','Family rule mismatch'] or 'needs architecture' in domain:stage='2 · Architecture review required'
        elif not topology.startswith('Consistent'):stage='3 · Topology/localization review required'
        elif not motif.startswith('Region-supported'):stage='4 · Motif-context review required'
        else:stage='5 · Cross-signal biological review required'
        host=value(r,'Orthology_Hsap_direct_orthologues','Hsap_orthologues')
        derived.append(dict(orthogroup=group,orthology_scope=state or 'Not reported',orthology_evidence='Mapped family-history evidence' if orth else 'Unresolved',schistosome_species_in_HOG=species_count,domain_evidence=domain,topology_evidence=topology,motif_context_evidence=motif,evidence_review_stage=stage,adhesome_interpretation='Not established by orthology; diagnostic architecture and biological context require review',priority_group=priority,host_orthology_flag='Human orthologues reported; assess selectivity separately' if host else 'No direct human orthologues reported; selectivity unassessed'))
    return pd.concat([frame.reset_index(drop=True),pd.DataFrame(derived)],axis=1)
