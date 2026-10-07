"""Shared functional zones for the family map and local matrix simulation."""
import json

ZONES = [
    {'id':'L1','name':'Integrin signalling','nodes':['inta','intb','integrin_ab','vkr1','fak','src','paxillin','ptppest','shc','grb2','nck'],
     'role':'Receptor engagement, FAK/Src mechanosensing and adaptor-mediated biochemical filtering.'},
    {'id':'L2','name':'Force transduction','nodes':['talin','kindlin','vinculin'],
     'role':'The talin–vinculin mechanical clutch connects integrin engagement to actin-generated tension; kindlin supports receptor activation.'},
    {'id':'L3','name':'Actin regulation','nodes':['ilk','pinch','parvin','actinin','filamin','zyxin','cofilin','profilin','actin'],
     'role':'Actin attachment, cross-linking, remodelling and ILK–PINCH-associated scaffold coupling. Parvin remains a reference-only component.'},
]
FUNCTIONS = [
    {'id':'mechanics','name':'Mechanotransduction & tensile strength','nodes':['collagen','laminin','vascular_context','integrin_ab','inta','intb','talin','kindlin','vinculin','actin','fak','src'],
     'role':'Ligand anchoring → talin exposure → vinculin reinforcement → actin-force feedback.'},
    {'id':'cytoskeleton','name':'Cytoskeletal organization','nodes':['talin','vinculin','ilk','pinch','parvin','actinin','filamin','zyxin','cofilin','profilin','actin'],
     'role':'Actin coupling, filament cross-linking and remodelling; the complete canonical IPP complex is not assigned.'},
    {'id':'migration','name':'Migration & traction','nodes':['fak','src','paxillin','ptppest','actinin','filamin','cofilin','profilin','actin'],
     'role':'Low-load protrusion and high-load traction are complementary model projections. Rac/Cdc42 and Rho/ROCK are reference pathway context.'},
    {'id':'growth','name':'Growth & survival','nodes':['fak','src','paxillin','shc','grb2','ilk','pinch','actin'],
     'role':'FAK/adaptor and ILK-associated coupling to ERK and Akt–mTOR reference pathways, expressed as dimensionless readouts.'},
    {'id':'reproduction','name':'Reproduction & development','nodes':['integrin_ab','intb','ilk','pinch','nck','vkr1'],
     'role':'Schistosome receptor-coupling context: Smβ-Int1–ILK–PINCH–Nck2–SmVKR1. Mammalian implantation is reference context, not a parasite endpoint.'},
]
SOURCES = [
    {'title':'Kanchanawong et al. (2010) · reference nanoscale architecture','url':'https://doi.org/10.1038/nature09621'},
    {'title':'del Rio et al. (2009) · force-exposed talin binding sites','url':'https://doi.org/10.1126/science.1162912'},
    {'title':'Gelmedin et al. (2017) · schistosome receptor-coupling context','url':'https://doi.org/10.1371/journal.ppat.1006147'},
]
ARCHITECTURE = {'zones':ZONES,'functions':FUNCTIONS,'sources':SOURCES,
                'coordinate_basis':'Functional reference schematic; no measured schistosome nanometre coordinates.',
                'reference_extensions':['VASP','Rac1/Cdc42–Arp2/3','RhoA–ROCK–myosin II','Ras–ERK','Akt–mTOR']}


def architecture_json():
    return json.dumps(ARCHITECTURE,ensure_ascii=False).replace('<','\\u003c')
