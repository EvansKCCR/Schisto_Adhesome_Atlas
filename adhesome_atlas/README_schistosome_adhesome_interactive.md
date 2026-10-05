# Schistosome Integrin-Adhesome Visualization

## Purpose

This interactive visualization presents an **evidence-calibrated working model of the schistosome integrin adhesome**. It is intended to:

- organize the current schistosome adhesome family inventory into biologically interpretable extracellular, membrane, membrane-proximal, cytoskeletal, scaffold, signalling, and actin-regulatory layers;
- distinguish **family presence** from **interaction evidence**;
- display conserved adhesome relationships that are plausible in schistosomes without presenting transferred relationships as experimentally validated parasite biology;
- identify unresolved components and testable network hypotheses;
- provide a transparent framework for selecting interactions and protein families for structural, localization, biochemical, genetic, and functional validation.

The visualization is a **hypothesis map**, not a validated pathway diagram, kinetic model, or demonstration that all displayed proteins assemble into one endogenous complex.

The diagram is editable SVG: drag any family node to rearrange its edges, use **Center node names** to put names in the middle of nodes, reset the layout, or export the current arrangement as a vector SVG.

## Current biological hypothesis

The working hypothesis is that schistosomes possess a conserved but parasite-adapted integrin-associated network that may couple extracellular and host-vascular inputs to:

1. candidate αβ-integrin receptor complexes;
2. membrane-proximal adhesion machinery;
3. actin attachment and remodelling;
4. focal-adhesion-like scaffolding and FAK/Src-associated signalling; and
5. an experimentally informed *Schistosoma mansoni* receptor-coupling branch involving Smβ-Int1, SmILK, SmPINCH, SmNck2, and the membrane receptor SmVKR1.

This hypothesis does not require the schistosome network to be identical to a canonical vertebrate focal adhesion. The visualization allows conserved components to be retained while clearly marking parasite-specific evidence, missing components, and unresolved relationships.

## Data represented

The current visualization contains **272 family-assignment records across 22 audit families**, distributed across *S. haematobium*, *S. japonicum*, and *S. mansoni*.

Node counts represent the number of records assigned to each audit family in the current supplied library. They should be interpreted as **family-inventory counts**, not as evidence that:

- every candidate is expressed in the relevant tissue or life stage;
- every candidate is localized to an adhesion structure;
- every family member binds the displayed partner;
- all candidates participate in one molecular complex; or
- copy number is proportional to pathway activity or biological importance.

The network therefore separates **candidate-family assignment** from **functional validation**.

## Evidence classes

### 1. Established reference architecture or complex relationship

These edges represent well-established relationships in canonical integrin adhesomes, such as integrin α/β receptor organization, β-integrin-tail association with talin or kindlin, talin–vinculin coupling, and actin binding by talin, vinculin, α-actinin, or filamin.

Their inclusion indicates that the corresponding schistosome families are present and that the relationship is structurally or evolutionarily plausible. It does **not** constitute direct experimental proof of the interaction in schistosomes.

### 2. Reference-inferred relationship

These edges are transferred from characterized metazoan adhesomes because the relevant schistosome candidate families are present. Examples include candidate collagen-like or laminin-like ligand relationships, kindlin–ILK module placement, and some scaffold or actin-regulatory associations.

Such edges are hypotheses requiring parasite-specific confirmation.

### 3. Experimentally informed *S. mansoni* relationship

The strongest parasite-specific interaction context is the reported cooperation between the membrane receptors Smβ-Int1 and SmVKR1 through SmILK, SmPINCH, and SmNck2. Co-expression and co-immunoprecipitation experiments in *Xenopus* oocytes supported formation of a Smβ-Int1–SmILK–SmPINCH–SmNck2–SmVKR1 complex and activation of SmVKR1 ([Gelmedin et al., 2017](https://doi.org/10.1371/journal.ppat.1006147)).

In this visualization:

- **SmVKR1 is represented as a plasma-membrane Venus kinase receptor**, not as an adaptor protein;
- SmILK, SmPINCH, and SmNck2 are represented as proposed intracellular bridging components;
- the relationship is treated as experimentally informed for *S. mansoni*;
- the evidence is not automatically generalized to every family member, paralogue, tissue, life stage, or other schistosome species; and
- heterologous complex formation is distinguished from demonstration of the complete endogenous complex in parasite tissue.

### 4. Hypothesis-only contextual relationship

These edges encode the broader hypothesis that vascular mechanics, endothelial contact, or other host-interface conditions may influence parasite adhesion and signalling.

They are included to make the biological hypothesis explicit, not because the current family inventory demonstrates a direct host–parasite interaction. No quantitative effect, ligand identity, force-response coefficient, or receptor specificity is assigned.

### 5. Unresolved reference component

A canonical component may be displayed as unresolved when it is relevant to reference adhesome architecture but is not supported in the current audit-family inventory. For example, parvin may be shown to expose the expected ILK–PINCH–parvin architecture while making clear that a complete canonical IPP complex is not asserted for the current schistosome dataset.

## Underlying assumptions

### Family assignment

1. The current classification pipeline provides a defensible family-level inventory based on the available sequence, architecture, orthology, motif, topology, localization, and related evidence.
2. Family membership establishes plausible molecular capacity but does not establish pathway recruitment or interaction.
3. Closely related proteins and paralogues may have different functions, partners, expression patterns, or tissue distributions.

### Integrin receptor layer

4. Schistosome integrin-α and integrin-β candidates may form functional heterodimers.
5. Exact physiological α/β pairings remain unresolved unless supported by separate structural or experimental evidence.
6. Candidate collagen-like and laminin-like families are plausible extracellular ligand classes, but their presence does not establish direct binding to schistosome integrins.
7. Host-derived ligands and parasite-derived ligands are not treated as interchangeable without direct evidence.

### Membrane-proximal and cytoskeletal layers

8. Conserved talin, kindlin, ILK, PINCH-like, vinculin, filamin, α-actinin, paxillin-like, zyxin-like, actin, and cofilin families provide a plausible basis for integrin-proximal coupling and cytoskeletal organization.
9. Reference-supported domain or family compatibility is sufficient to display a candidate relationship, but not to label it as a confirmed endogenous interaction.
10. The absence of a resolved parvin family prevents assertion of a complete canonical IPP complex in the present reconstruction.

### Signalling layer

11. FAK- and Src-family candidates support a plausible focal-adhesion-like signalling module, but family assignment does not establish activation by schistosome integrins.
12. Directional arrows indicate proposed information flow or regulatory convention, not measured reaction order, phosphorylation kinetics, or pathway flux.
13. Shc, Grb2, Nck, PTP-PEST, and related adaptor or regulatory families are not assigned interactions solely because they occur in the inventory.

### SmVKR1 receptor-coupling branch

14. SmVKR1 is a membrane receptor and is kept in the plasma-membrane layer.
15. SmILK, SmPINCH, and SmNck2 are treated as proposed bridging molecules between Smβ-Int1 and SmVKR1 in *S. mansoni*.
16. This receptor-coupling branch is relevant to reproductive biology, but the visualization does not assume that it is active in every cell, sex, stage, or species.
17. Cross-species transfer of the *S. mansoni* relationship to *S. haematobium* or *S. japonicum* remains a testable comparative hypothesis.

### Host-vascular adaptation

18. Schistosome residence within the vasculature provides a biological rationale for examining adhesion and mechanosensory adaptation.
19. The visualization does not claim that haemodynamic force directly activates any displayed receptor or pathway.
20. “Parasite-adapted” means that conserved adhesome components may have been functionally reweighted or connected to parasite-specific physiological processes. It does not imply that the direction or magnitude of that adaptation has been experimentally measured.

## What the visualization does not show

The visualization should not be used to infer:

- experimentally measured binding affinity;
- protein abundance or expression;
- tissue or subcellular localization unless supplied independently;
- temporal activation order;
- phosphorylation state;
- force magnitude or mechanosensitivity;
- essentiality;
- druggability;
- pathway flux;
- validated host–parasite binding;
- one-to-one orthology to individual vertebrate paralogues; or
- assembly of all displayed nodes into a single complex.

## How to interpret the display

- **Nodes** represent audit families, reference-context components, or explicit hypothesis-context entities.
- **Node counts** represent current family-assignment records in the order *S. haematobium* / *S. japonicum* / *S. mansoni*.
- **Solid relationships** indicate established reference architecture or an experimentally informed complex relationship, as described in the node or edge metadata.
- **Dashed relationships** indicate reference transfer, unresolved reference architecture, or hypothesis-only context.
- **Directional arrows** indicate proposed signalling or regulatory flow, not kinetic proof.
- **Reference-only nodes** expose gaps in the current reconstruction rather than filling those gaps with unsupported candidates.
- Selecting a node or edge displays its provenance, evidence class, transfer basis, species scope, and interpretive limitation.

### Linked Atlas simulation

In the Atlas Introduction, select a map node and choose **Explore downstream simulation** in its evidence panel. The linked simulator opens in the same workspace, with a **Map** tab to return to the selected network. It compares the schistosome hypothesis and canonical reference under the same inputs.

The node-to-simulator link selects an illustrative perturbation of the represented input or module: reduced candidate extracellular input, low-affinity integrin state, reduced talin–kindlin recruitment, reduced tension, or the existing ILK, FAK/Src, or VKR1 branch switches. The simulator shows the mapping rationale and the schistosome baseline-to-scenario change. Other nodes retain the baseline with a statement that no family-specific model parameter exists. This link does not add experimental support to an edge or infer a protein-specific effect.

## Appropriate uses

The visualization is suitable for:

- communicating the current schistosome adhesome hypothesis;
- auditing whether network edges match available evidence;
- distinguishing conserved architecture from parasite-specific evidence;
- identifying missing or unresolved families;
- prioritizing candidate interactions for validation;
- preparing manuscript figures and supplementary interactive resources; and
- generating explicitly testable experimental questions.

## Primary biological reference

- Gelmedin V, Morel M, Hahnel S, et al. Evidence for Integrin–Venus Kinase Receptor 1 Alliance in the Ovary of *Schistosoma mansoni* Females Controlling Cell Survival. *PLOS Pathogens*. 2017;13:e1006147. [Read the article](https://doi.org/10.1371/journal.ppat.1006147).

## Disclaimer

This resource is intended for scientific exploration and hypothesis generation. It does not replace experimental validation. Absence from the visualization should not be interpreted as biological absence, and inclusion should not be interpreted as proof of interaction, localization, pathway membership, essentiality, or therapeutic suitability.
