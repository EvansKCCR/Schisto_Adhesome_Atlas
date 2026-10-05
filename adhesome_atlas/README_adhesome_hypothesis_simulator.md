# Schistosome Integrin-Adhesome Hypothesis Simulator

## Overview

This interactive model provides a **qualitative hypothesis-testing framework** for exploring how a candidate schistosome integrin adhesome could connect extracellular or host-vascular cues to integrin-associated mechanotransduction, cytoskeletal organization, survival, and reproduction.

The atlas displays a schistosome hypothesis beside a canonical metazoan reference scenario, using the same input controls. The schistosome panel offers three explicit system assumptions:

1. **Parasite-adapted adhesome effect**
2. **Host-like canonical adhesome effect**
3. **Neutral comparative baseline**

The model is not intended to reproduce experimentally measured signalling kinetics. Instead, it converts a reconstructed interaction network into testable causal scenarios that can guide experimental prioritization.

## Scientific Rationale

The central hypothesis is that schistosomes possess an integrated adhesion network that links extracellular or host-vascular conditions with intracellular signalling and mechanotransduction pathways involved in parasite survival and reproduction.

The model combines:

- candidate extracellular matrix inputs;
- a putative integrin αβ receptor complex;
- talin- and kindlin-associated membrane-proximal coupling;
- actomyosin-dependent adhesion maturation;
- FAK/Src-associated signalling;
- a hypothesized ILK–PINCH–Nck2 connection to VKR1-associated reproductive signalling.

Experimental work in *Schistosoma mansoni* supports an association between Smβ-Int1, SmILK, SmPINCH, SmNck2, and SmVKR1. However, the broader pan-schistosome adhesome, endogenous ligands, physiological integrin pairings, and most network edges remain hypotheses requiring experimental validation.

## Relevance of the Model

### 1. Distinguishing conserved and parasite-adapted adhesome logic

The **host-like context** represents a canonical focal-adhesion assumption in which extracellular engagement promotes integrin activation, talin–kindlin coupling, force-dependent adhesion maturation, and predominantly FAK/Src-associated signalling.

The **parasite-adapted context** tests whether schistosomes may retain parts of this conserved structural machinery while redistributing signalling toward parasite-relevant physiological outputs, particularly reproduction and survival through the proposed ILK–PINCH–Nck2–VKR1 branch.

The **neutral baseline** balances the mechanical and reproductive contributions without assuming either a canonical host-like organization or a specialized parasite-adapted organization.

These contexts are comparative assumptions. They are not experimentally measured differences between host and parasite systems.

### 2. Converting a static network into causal predictions

A reconstructed network identifies candidate components and plausible interactions but does not indicate how the system may respond to perturbation. The simulation expresses qualitative predictions such as:

- FAK/Src inhibition reduces the canonical kinase branch while preserving initial receptor engagement and structural coupling.
- ILK–PINCH–Nck2 disruption weakens the proposed connection between the integrin-associated system and reproductive signalling.
- VKR1 inhibition preferentially reduces the reproductive contribution without necessarily eliminating structural integrin–cytoskeletal coupling.
- Reduced talin–kindlin recruitment limits membrane-proximal adaptor coupling.
- Reduced actomyosin tension limits force-dependent maturation even when receptor engagement is retained.

These predictions can help prioritize RNA interference, inhibitor studies, localization experiments, interaction assays, and phenotype measurements.

### 3. Integrating different evidence levels conservatively

The model brings together evidence that should remain clearly separated:

- **Family-level evidence:** computational support for candidate integrin, talin, kindlin, ILK, cytoskeletal, scaffold, FAK, and Src families.
- **Interaction evidence:** experimentally reported or computationally transferred associations among candidate components.
- **Functional evidence:** observed or predicted effects on cytoskeletal organization, survival, reproduction, and egg production.
- **Hypothetical relationships:** unvalidated ligand–receptor interactions, integrin αβ pairings, species-level dynamics, and pathway weights.

Protein-family identity does not establish recruitment into an endogenous schistosome adhesion complex. Likewise, a transferred interaction does not establish a direct physical interaction in schistosomes.

### 4. Generating contrasting biological predictions

Under a **host-like assumption**, increasing ligand engagement, integrin activation, adaptor recruitment, and mechanical tension produces stronger adhesion maturation and FAK/Src output.

Under a **parasite-adapted assumption**, perturbation of ILK, PINCH, Nck2, or VKR1 is expected to produce a relatively stronger reproductive or survival phenotype, even if changes in canonical focal-adhesion maturation are modest.

The comparison therefore asks whether schistosomes:

- retain a reduced canonical focal-adhesion pathway;
- use a broadly host-like mechanotransduction system;
- or have repurposed conserved adhesion components toward parasite-specific physiological outputs.

## Experimental Questions Supported by the Model

The model can help organize experiments addressing the following questions:

1. Do candidate integrins, ILK, PINCH, Nck2, and VKR1 colocalize in reproductive or other relevant tissues?
2. Do the predicted proteins form direct or indirect complexes?
3. Does adhesion-related stimulation alter FAK/Src or VKR1-associated phosphorylation?
4. Are candidate adhesome components required for actin organization or mechanical responses?
5. Do perturbations affect oocyte survival, egg production, migration, attachment, or parasite viability?
6. Are structural adhesion phenotypes separable from reproductive signalling phenotypes?
7. Are these responses conserved across *S. haematobium*, *S. japonicum*, and *S. mansoni*?

## Model Controls

### Species context

- Pan-schistosome
- *S. haematobium*
- *S. japonicum*
- *S. mansoni*

Species selection currently changes the displayed candidate context but does not represent experimentally fitted species-specific kinetics.

The reference-proteome selector offers *H. sapiens*, *M. musculus*, *X. laevis*, *D. melanogaster*, and *C. elegans* as orthology contexts. It changes the reference label; all five use the same illustrative canonical model coefficients.

### Candidate extracellular input

- Mixed candidate ECM input
- Collagen-like, motif-prioritized input
- Laminin-like, motif-prioritized input
- Hypothetical host-vascular interface

The endogenous schistosome integrin ligands remain unresolved. These options represent candidate input classes rather than confirmed receptor ligands.

### System context

- Parasite-adapted adhesome effect
- Host-like canonical adhesome effect
- Neutral comparative baseline

### Continuous parameters

- Ligand availability
- Initial integrin conformational state
- Talin–kindlin recruitment
- Actomyosin tension

### In-silico perturbations

- Control
- FAK/Src branch inhibition
- ILK–PINCH–Nck2 coupling disruption
- VKR1 reproductive-branch inhibition

## Interpreting the Outputs

The simulator displays normalized trajectories for:

- integrin activation;
- adaptor coupling;
- force-dependent adhesion maturation;
- combined kinase output.

The curves indicate assumed relative behaviour within the model. They should not be interpreted as measured concentrations, phosphorylation levels, binding affinities, time constants, or biological effect sizes.

A result affecting both structural coupling and reproductive signalling would be compatible with an integrated adhesome hypothesis. A predominantly reproductive phenotype would provide greater support for parasite-adapted pathway weighting. A strong tension-dependent FAK/Src response would be more compatible with canonical host-like organization.

## Key Limitations

The current implementation does not establish:

- endogenous ligand identity;
- physiological integrin αβ pairing;
- direct recruitment of all candidate proteins into one complex;
- experimentally measured pathway strengths;
- kinetic or binding constants;
- species-specific signalling rates;
- the relative contribution of FAK/Src and VKR1-associated outputs;
- tissue-specific expression or localization;
- causal direction for most reconstructed network edges.

The numerical weights are intentionally illustrative and must not be treated as estimated biological parameters.

## Appropriate Use

Use this model to:

- make assumptions explicit;
- compare alternative network organizations;
- identify discriminating experiments;
- prioritize candidate perturbations;
- communicate the current working hypothesis;
- connect the computational adhesome reconstruction to an experimental validation plan.

Do not use this model to:

- claim quantitative pathway behaviour;
- infer clinical or therapeutic efficacy;
- present predicted interactions as experimentally validated;
- assign definitive endogenous ligands or receptor pairings;
- compare species using unmeasured kinetic effects.

## Path Toward Quantitative Fitting

The simulator could become a fitted biological model after suitable experimental data are generated. Useful calibration data would include:

- time-resolved phosphorylation measurements;
- dose-response data for pathway inhibitors;
- RNAi perturbation phenotypes;
- quantitative interaction measurements;
- expression and localization data;
- actin organization or force-response measurements;
- reproductive and survival outcomes.

These observations could be used to replace assumed pathway weights with estimated parameters and uncertainty intervals.

## Running the Simulator

On the Atlas **Introduction** page, select a node in the interactive adhesome map and choose **Explore downstream simulation**. The standalone file can also be opened in a modern web browser:

```text
schistosome_integrin_adhesome_hypothesis_simulator.html
```

The simulator is self-contained and does not require an external charting library.

### Linked mode in the Atlas

On the Introduction page, select a family or context node in the interactive adhesome map and choose **Explore downstream simulation**. The linked view loads a qualitative node-to-control scenario into this simulator and displays the baseline and selected final maturation/signalling scores. The same settings drive both schistosome and canonical-reference panels. Return to the map with the **Adhesome map** tab; manually adjusted simulator controls are retained until another node scenario is selected.

The link uses only controls already present in this model. Extracellular candidates map to a reduced availability proxy, integrin nodes to a low-affinity receptor state, talin/kindlin to reduced adaptor recruitment, selected cytoskeletal nodes to reduced tension, and ILK/PINCH/Nck, FAK/Src, or VKR1 nodes to their corresponding branch switches. Nodes without a direct model parameter leave the baseline unchanged. These are module-level thought experiments, not fitted protein-specific perturbations.

## Reference

Gelmedin V, Morel M, Hahnel S, et al. Evidence for Integrin–Venus Kinase Receptor 1 Alliance in the Ovary of *Schistosoma mansoni* Females Controlling Cell Survival. *PLOS Pathogens*. 2017;13(1):e1006147. [https://doi.org/10.1371/journal.ppat.1006147](https://doi.org/10.1371/journal.ppat.1006147)

## Disclaimer

This is a conceptual research tool. The parasite-adapted and host-like effects are explicit comparative assumptions, and all outputs are normalized qualitative simulations rather than experimentally fitted predictions.
