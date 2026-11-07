"""Regenerate the checked-in evidence exports and standalone Atlas views."""

from candidate_profiles import candidate_map_html, profile_payload
from data import ROOT, load
from library_refresh import _write_changed, refresh_family_html
from literature import CROSSWALK, MODEL_DIR, build_registry, tsv, write_registry
from research_priorities import load_brief, priority_trace
from simulator import SIMULATOR_FILE, simulator_html


def main():
    cohorts, books, motifs, *_ = load()
    candidates = cohorts['Adhesome candidates']
    registry = build_registry(ROOT, candidates, books[CROSSWALK])
    brief = load_brief(ROOT/'Target_prioritization.md')
    trace = priority_trace(brief, candidates, registry)

    catalogue_map = ROOT/'adhesome_network/Schistosome_adhesome_rebuilt.html'
    html = refresh_family_html(catalogue_map.read_text(encoding='utf-8'), candidates, ROOT, registry)
    html = candidate_map_html(html, profile_payload(candidates, books, motifs, literature=registry))
    simulator = ROOT/SIMULATOR_FILE
    simulation_html = simulator_html(simulator, candidates, registry)

    write_registry(ROOT, registry)
    _write_changed(ROOT/MODEL_DIR/'priority_reference_trace.tsv', tsv(trace))
    _write_changed(catalogue_map, html)
    _write_changed(simulator, simulation_html)
    print(f"{len(candidates):,} records, {candidates.sequence_id.nunique():,} proteins, "
          f"{len(registry['references'])} studies, {len(registry['protein_links'])} scoped links, "
          f"{len(registry['interactions'])} interaction records, {len(trace)} priority trace rows.")
    print(f"Standalone map {catalogue_map.stat().st_size:,} bytes. Simulator {simulator.stat().st_size:,} bytes.")


if __name__ == '__main__':
    main()
