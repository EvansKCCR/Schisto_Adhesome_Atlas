# Layered adhesion-matrix simulator

**Interactive hypothesis → Downstream simulation** compares a schistosome
lattice with a canonical reference. Each receptor site stores an I–T–V
association matrix and local scaffold and signalling states. I represents
ligand-engaged integrin αβ at the β-tail interface. The mechanics and
recruitment inputs use dimensionless units.

1. **Membrane-proximal signalling** contains integrin tails, kindlin, paxillin,
   FAK/Src and receptor-associated signalling.
2. **Force transduction and membrane–actin clutch** contains talin, vinculin
   and the ILK–PINCH–parvin scaffold.
3. **Actin regulation** contains F-actin, α-actinin, zyxin/Ajuba and Ena/VASP
   context. The local view shows the state of each component at the selected site.

The layers follow the organization described by Kanchanawong et al. (R15).
The diagram places proteins by functional role. Force-transmitting talin–actin
or IPP–actin links enable loading. At the exposure threshold the effective
talin–vinculin weight gains the editable amplification factor (R16).
An assembled actin-attached clutch reinforces the site. Unloaded sites relax
and dissociation or overload clears all occupancy at the affected site.

## Assembly modules

- **Kindlin–IPP.** Kindlin occupies engaged integrin sites. ILK recruits PINCH
  and parvin through separate assembly conditions. Occupancy of kindlin, ILK,
  PINCH and parvin enables IPP–actin coupling and stabilization (R17–R19).
- **SmVKR1.** The *S. mansoni* context uses an independent Smβ-Int1–ILK–PINCH–Nck2
  assembly gate and a separate VKR1 engagement gate (R02). ILK and PINCH
  occupancy is shared with IPP. This branch is available for the pan-schistosome
  and *S. mansoni* settings. The canonical panel uses the metazoan modules.
- **Signalling and actin.** FAK/Src follows normalized load (R15, R21). Paxillin
  and actin regulators have configurable recruitment (R15, R20).
  Optional gonadal kinase/Rho and PKC/MAPK readouts scale the appropriate
  pathway context (R03–R07).

Open **Layered assembly modules and parameters** to configure the branches.
Clear force-transmitting talin/actin linkage and disable IPP to reproduce the
original I–T–V structural loading rule. **Mechanism literature and library
candidates** provides the rule, condition, variables, origin, study and DOI.
The site view, trajectory, and matrix inspectors update together.

## Candidate paths and exports

Click a family or protein on the interactive map, then use **Simulate candidate
and path**. The profile remains visible. Linked choices can reduce the relevant
recruitment probability. **Use highlighted path for downstream coupling**
controls the contextual gates. The baseline uses the same selected path and seed.

The JSON export contains both paired random streams' seed basis, weights, active
rule IDs, parameters, local states and trajectories, selected accession and path,
bibliography and source hashes. CSV exports summarize each timestep, including
IPP and bridge occupancy. The seed and parameter values support repeatable
comparisons. Rule definitions are in `data/literature/simulator_mechanisms.json`.
