"""Detect primary-file updates while the Atlas is open; preserve valid UI selections."""


def reconcile_selections(state,candidates):
    options={'catalogue_species':sorted(candidates.species.unique()),'catalogue_families':sorted(candidates.family.unique())}
    previous=state.get('atlas_option_snapshot',{})
    for key,allowed in options.items():
        if key in state:
            chosen=list(state[key])
            state[key]=allowed if key=='catalogue_species' and set(chosen)==set(previous.get(key,chosen)) else [v for v in chosen if v in allowed]
    ids=set(candidates.sequence_id)
    if state.get('map_candidate') and state['map_candidate'] not in ids:state['map_candidate']=''
    if state.get('dossier_protein') not in ids:state.pop('dossier_protein',None)
    state['atlas_option_snapshot']=options


def watch_sources(loaded_signature):
    import hashlib
    import json
    import streamlit as st
    from data import fingerprint

    @st.fragment(run_every='30s')
    def monitor():
        if fingerprint()!=loaded_signature:
            st.rerun()  # Full app refresh, including cached catalogue/profile inputs.
        version=hashlib.sha256(json.dumps(loaded_signature).encode()).hexdigest()[:16]
        st.markdown('<span id="atlas-source-status" data-source-version="'+version+'" style="font-size:12px;color:#526760">Automatic source refresh · checks every 30 seconds</span>',unsafe_allow_html=True)
    monitor()
