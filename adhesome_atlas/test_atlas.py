"""Run: python adhesome_atlas/test_atlas.py"""
from pathlib import Path
from streamlit.testing.v1 import AppTest
from data import load, fasta_export, ROOT, source_files
from networks import load_network

def main():
    cohorts, books, motifs, sequences, memberships, raw, topology, conflicts = load()
    assert len(cohorts['Adhesome candidates']) == 597
    assert cohorts['All screening hypotheses'].sequence_id.nunique() == 3305
    assert len(motifs) == 406
    assert not conflicts, conflicts
    for label, frame in cohorts.items():
        missing = set(frame.sequence_id)-sequences.keys()
        mismatch = [(r.sequence_id, r.length, len(sequences[r.sequence_id])) for r in frame.itertuples() if r.sequence_id in sequences and int(r.length) != len(sequences[r.sequence_id])]
        print(label, 'records', len(frame), 'proteins',frame.sequence_id.nunique(),'missing FASTA',len(missing),'length mismatch',len(mismatch), flush=True)
        assert not mismatch
    assert all(key not in sequences or len(states)==len(sequences[key]) for key,states in topology.items())
    assert set(motifs.sequence_id) <= sequences.keys()
    assert all(1 <= r.start <= r.end <= len(sequences[r.sequence_id]) for r in motifs.itertuples())
    assert len(fasta_export(['Shae__MS3_00000278']*2,sequences).split('>'))==2
    app = AppTest.from_file(str(Path(__file__).with_name('app.py')),default_timeout=60).run()
    assert not app.exception, app.exception
    for cohort in cohorts:
        app.sidebar.selectbox[0].set_value(cohort).run()
        for page in app.sidebar.radio[0].options:
            app.sidebar.radio[0].set_value(page).run()
            assert not app.exception, [(e.message) for e in app.exception]
            print('PASS',cohort,page,flush=True)
    app.sidebar.radio[0].set_value('Components').run()
    for view in app.sidebar.radio[1].options:
        app.sidebar.radio[1].set_value(view).run()
        assert not app.exception, [e.message for e in app.exception]
        print('PASS Components',view,flush=True)
    app.sidebar.radio[1].set_value('Candidate catalogue').run()
    app.sidebar.text_input[0].set_value('NO_MATCH_XYZ_012345').run()
    assert not app.exception and any('No candidates' in item.value for item in app.info)
    app.sidebar.text_input[0].set_value('[').run()
    assert not app.exception
    app.sidebar.text_input[0].set_value('').run()
    app.sidebar.multiselect[0].set_value([]).run()
    assert not app.exception and any('No candidates' in item.value for item in app.info)
    app.sidebar.radio[0].set_value('Interactions').run()
    next(r for r in app.radio if r.label == 'Network workspace').set_value('Species STRING explorer').run()
    for code, count in [('Shae',164),('Sjap',469),('Sman',274)]:
        nodes,edges,annotations = load_network(code,cohorts['Adhesome candidates'])
        assert len(edges)==count
        assert set(edges.node1_string_id)|set(edges.node2_string_id) <= set(nodes.identifier)
        app.selectbox(key='interactions_species').set_value(code).run()
        for mode in ['Family','STRING localization','DeepLoc localization','Original STRING colors']:
            app.selectbox(key='interactions_color').set_value(mode).run()
            assert not app.exception, [e.message for e in app.exception]
        print('PASS network colors',code,flush=True)
    app.slider(key='interactions_score').set_value(1.0).run()
    app.checkbox(key='interactions_isolates').set_value(False).run()
    assert not app.exception
    print('PASS empty filters and literal search; source files:',len(source_files()),flush=True)

if __name__ == '__main__':
    main()
