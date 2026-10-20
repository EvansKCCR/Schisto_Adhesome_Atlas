# Linked adhesion-matrix simulator

The simulator file is `adhesome_network/schistosome_integrin_adhesome_hypothesis_simulator.html`. It is available from the Introduction map through **Explore downstream simulation**, and as a tab within that linked viewer.

The model assembles local integrin–talin–vinculin adjacency matrices with force-dependent talin exposure and actin feedback. Species inventory is recalculated from current Supported candidates. All seven schistosome species are available; reference context names are read from the current orthology results. Framework and custom weights are explicit conceptual parameters. Removed STRING exports are never loaded, and human-reference interaction counts are not interpreted as binding affinities.

Family scenarios represent the coupling proxies defined in `linked_explorer.py`. Families without an explicit mechanism open the baseline and state that additional simulation information will be added when available. Inventory availability and centrality do not establish biological essentiality or a fitted kinetic model.


## Candidate/path-linked exploration

The linked viewer keeps the candidate profile visible while showing the simulator, and optionally shows the map and simulator together. Start by clicking a node; candidate search is not required. Candidate and highlighted-path changes synchronize through source-checked iframe messages. Structured candidate and path context is retained in simulation exports.

Path gating is an explicit hypothesis layer: FAK plus Src opens the FAK gate; ILK plus PINCH plus Nck opens the bridge; relevant selected families open migration, growth and cytoskeletal projections. VKR1 requires its context node and the S. mansoni species context. Family-specific perturbation controls are combined with these gates without reopening an excluded branch. An unreachable route closes the downstream gates. The I–T–V assembly rules are retained. The same-seed baseline uses the same path gates; **Use highlighted path for downstream coupling** can be disabled to apply only the selected-family mechanism.

The complete candidate profile remains independently browsable and downloadable in the persistent side panel. Run `python test_linked_context.py` for synchronization, gate, species, source-message and real matrix-engine checks.
