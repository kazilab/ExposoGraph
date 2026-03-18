"""Curated reference gene panels and activity scores for ExposoGraph.
"""

from __future__ import annotations

from .models import KnowledgeGraph, Node, NodeType

NCBI_GENE_IDS: dict[str, str] = {
    "ABCB1": "5243",
    "ABCC2": "1244",
    "ABCG2": "9429",
    "CYP1A1": "1543",
    "CYP1A2": "1544",
    "CYP1B1": "1545",
    "CYP2A6": "1548",
    "CYP2A13": "1553",
    "CYP2C19": "1557",
    "CYP2C9": "1559",
    "CYP2D6": "1565",
    "CYP2E1": "1571",
    "CYP3A4": "1576",
    "EPHX1": "2052",
    "ERCC2": "2068",
    "GSTM1": "2944",
    "GSTP1": "2950",
    "GSTT1": "2952",
    "MGMT": "4255",
    "NAT1": "6530",
    "NAT2": "10",
    "NQO1": "1728",
    "OGG1": "4968",
    "SULT1A1": "6817",
    "UGT1A1": "54658",
    "UGT2B7": "7364",
    "XPC": "7508",
    "XRCC1": "7515",
}

DNA_REPAIR_CLASSES: dict[str, str] = {
    "XRCC1": "DNA Repair (BER)",
    "OGG1": "DNA Repair (BER)",
    "XPC": "DNA Repair (NER)",
    "ERCC2": "DNA Repair (NER)",
    "MGMT": "DNA Repair (Direct Reversal)",
}


def _ncbi_gene_ref(symbol: str) -> dict[str, str]:
    gene_id = NCBI_GENE_IDS[symbol]
    return {
        "source_db": "NCBI Gene",
        "record_id": gene_id,
        "citation": f"NCBI Gene record for {symbol} (Homo sapiens)",
        "url": f"https://www.ncbi.nlm.nih.gov/gene/{gene_id}",
        "evidence": "Canonical human gene identifier and nomenclature.",
    }


def _gtex_ref(symbol: str, tissue: str) -> dict[str, str]:
    return {
        "source_db": "GTEx",
        "record_id": symbol,
        "citation": f"GTEx Portal expression profile for {symbol}",
        "url": f"https://gtexportal.org/home/gene/{symbol}",
        "tissue": tissue,
        "evidence": "Human tissue-expression context used to seed the panel tissue field.",
    }


def _clinpgx_ref(symbol: str) -> dict[str, str]:
    return {
        "source_db": "ClinPGx",
        "record_id": symbol,
        "citation": f"ClinPGx gene resource for {symbol}",
        "url": f"https://www.clinpgx.org/gene/{symbol}",
        "evidence": "Pharmacogenomics and xenobiotic-response gene resource.",
    }


def _pharmvar_ref(symbol: str) -> dict[str, str]:
    return {
        "source_db": "PharmVar",
        "record_id": symbol,
        "citation": f"PharmVar allele definition resource for {symbol}",
        "url": f"https://www.pharmvar.org/gene/{symbol}",
        "evidence": "Star-allele nomenclature and haplotype definition resource.",
    }


def _ctd_ref(symbol: str, repair_class: str) -> dict[str, str]:
    return {
        "source_db": "CTD",
        "record_id": symbol,
        "citation": f"Comparative Toxicogenomics Database record for {symbol}",
        "url": f"https://ctdbase.org/detail.go?type=gene&acc={symbol}",
        "evidence": f"Toxicogenomic context supporting the {repair_class} assignment.",
    }


def _pubmed_ref(pmid: str, citation: str, evidence: str) -> dict[str, str]:
    return {
        "source_db": "PubMed",
        "record_id": pmid,
        "pmid": pmid,
        "citation": citation,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "evidence": evidence,
    }


def _gene_provenance(symbol: str, *, tissue: str, repair_class: str | None = None) -> list[dict[str, str]]:
    records = [_ncbi_gene_ref(symbol), _gtex_ref(symbol, tissue)]
    if repair_class:
        records.append(_ctd_ref(symbol, repair_class))
    else:
        records.append(_clinpgx_ref(symbol))
    return records


def _gene_entry(
    symbol: str,
    *,
    detail: str,
    tissue: str,
    role: str,
    phase: str | None = None,
    group: str | None = None,
    label: str | None = None,
) -> dict:
    return {
        "id": symbol,
        "label": label or symbol,
        "detail": detail,
        "tissue": tissue,
        "role": role,
        "phase": phase,
        "group": group,
        "provenance": _gene_provenance(symbol, tissue=tissue, repair_class=group),
    }


def _activity_score_meta(
    evidence_basis: str,
    note: str,
    *references: dict[str, str],
) -> dict[str, object]:
    return {
        "evidence_basis": evidence_basis,
        "note": note,
        "references": list(references),
    }

# ── Tier 1: Core Carcinogen-Metabolizing Enzyme Panel (13 genes) ─────────

TIER1_GENES: list[dict] = [
    _gene_entry(
        "CYP1A1",
        phase="I",
        role="Activation",
        detail="PAH diol-epoxide formation; AhR-inducible; extrahepatic expression",
        tissue="lung, placenta, lymphocytes",
    ),
    _gene_entry(
        "CYP1A2",
        phase="I",
        role="Activation",
        detail="HCA and aromatic amine activation; AhR-inducible; hepatic",
        tissue="liver",
    ),
    _gene_entry(
        "CYP1B1",
        phase="I",
        role="Activation",
        detail="PAH and estrogen activation; 4-OH-estradiol formation",
        tissue="breast, prostate, uterus, lung",
    ),
    _gene_entry(
        "CYP2A6",
        phase="I",
        role="Activation",
        detail="NNK and nitrosamine activation; nicotine metabolism",
        tissue="liver, nasal mucosa",
    ),
    _gene_entry(
        "CYP2E1",
        phase="I",
        role="Activation",
        detail="Small-molecule carcinogen activation; ethanol, benzene, NDMA",
        tissue="liver, lung",
    ),
    _gene_entry(
        "CYP3A4",
        phase="I",
        role="Activation",
        detail="Aflatoxin B1 8,9-epoxidation; broad substrate range",
        tissue="liver, intestine",
    ),
    _gene_entry(
        "GSTM1",
        phase="II",
        role="Detoxification",
        detail="GSH conjugation of PAH diol-epoxides and AFB1-epoxide; null polymorphism common",
        tissue="liver, lung",
    ),
    _gene_entry(
        "GSTT1",
        phase="II",
        role="Detoxification",
        detail="GSH conjugation of small electrophiles; null polymorphism common",
        tissue="liver, kidney, blood cells",
    ),
    _gene_entry(
        "GSTP1",
        phase="II",
        role="Detoxification",
        detail="GSH conjugation of BPDE and other PAH diol-epoxides",
        tissue="lung, brain, placenta",
    ),
    _gene_entry(
        "NAT2",
        phase="II",
        role="Mixed",
        detail="N-acetylation of aromatic amines; rapid vs slow acetylator phenotypes",
        tissue="liver, intestine",
    ),
    _gene_entry(
        "EPHX1",
        phase="II",
        role="Mixed",
        detail="Microsomal epoxide hydrolysis; both activation and detoxification roles",
        tissue="liver, lung",
    ),
    _gene_entry(
        "UGT1A1",
        phase="II",
        role="Detoxification",
        detail="Glucuronidation of PAH metabolites and bilirubin",
        tissue="liver, intestine",
    ),
    _gene_entry(
        "NQO1",
        phase="II",
        role="Detoxification",
        detail="Two-electron quinone reduction; prevents ROS from redox cycling",
        tissue="liver, lung, colon",
    ),
]

# ── Tier 2: Extended Gene Panel (15 genes) ───────────────────────────────

TIER2_GENES: list[dict] = [
    # Phase II
    _gene_entry(
        "SULT1A1",
        phase="II",
        role="Detoxification",
        detail="Sulfation of phenolic compounds, HCA intermediates, PAH metabolites",
        tissue="liver, GI tract, platelets, brain",
    ),
    _gene_entry(
        "NAT1",
        phase="II",
        role="Mixed",
        detail="O-acetylation and N-acetylation of aromatic/heterocyclic amines in peripheral tissues",
        tissue="bladder, colon, breast, lung",
    ),
    _gene_entry(
        "UGT2B7",
        phase="II",
        role="Detoxification",
        detail="Glucuronidation of steroid hormones, carcinogen metabolites",
        tissue="liver, kidney, GI tract, mammary",
    ),
    # Phase III transporters
    _gene_entry(
        "ABCB1",
        phase="III",
        role="Transport",
        detail="P-gp; ATP-driven efflux of hydrophobic xenobiotics and carcinogens",
        tissue="liver, intestine, kidney, BBB, placenta",
    ),
    _gene_entry(
        "ABCC2",
        phase="III",
        role="Transport",
        detail="MRP2; export of GSH/glucuronide/sulfate conjugates of carcinogen metabolites",
        tissue="liver, kidney, intestine",
    ),
    _gene_entry(
        "ABCG2",
        phase="III",
        role="Transport",
        detail="BCRP; efflux of PAHs, PhIP, porphyrins",
        tissue="intestine, liver, placenta, mammary, BBB",
    ),
    # DNA repair
    _gene_entry(
        "XRCC1",
        group=DNA_REPAIR_CLASSES["XRCC1"],
        role="Repair",
        detail="BER scaffold protein; coordinates repair of oxidative/alkylation DNA damage",
        tissue="ubiquitous",
    ),
    _gene_entry(
        "XPC",
        group=DNA_REPAIR_CLASSES["XPC"],
        role="Repair",
        detail="GG-NER damage sensor; recognizes bulky DNA adducts from PAHs",
        tissue="ubiquitous",
    ),
    _gene_entry(
        "ERCC2",
        label="ERCC2/XPD",
        group=DNA_REPAIR_CLASSES["ERCC2"],
        role="Repair",
        detail="NER helicase; unwinds DNA at damage sites for bulky adduct excision",
        tissue="ubiquitous",
    ),
    _gene_entry(
        "OGG1",
        group=DNA_REPAIR_CLASSES["OGG1"],
        role="Repair",
        detail="8-oxoguanine DNA glycosylase; excises oxidative DNA damage (8-oxodG)",
        tissue="ubiquitous (nuclear + mitochondrial)",
    ),
    _gene_entry(
        "MGMT",
        group=DNA_REPAIR_CLASSES["MGMT"],
        role="Repair",
        detail="Direct reversal of O6-alkylguanine; single-use suicidal repair enzyme",
        tissue="liver, colon, lung, brain",
    ),
    # Additional CYPs (PGx overlap)
    _gene_entry(
        "CYP2C9",
        phase="I",
        role="Mixed",
        detail="Oxidation of some PAH metabolites; major drug-metabolizing CYP",
        tissue="liver, intestine",
    ),
    _gene_entry(
        "CYP2C19",
        phase="I",
        role="Mixed",
        detail="Minor procarcinogen activation; possible nitrosamine metabolism",
        tissue="liver, intestine",
    ),
    _gene_entry(
        "CYP2D6",
        phase="I",
        role="Mixed",
        detail="Minor NNK activation; important for dual PGx/carcinogen-risk reporting",
        tissue="liver, brain, lung, GI tract",
    ),
    _gene_entry(
        "CYP2A13",
        phase="I",
        role="Activation",
        detail="Primary lung NNK-metabolizing CYP; tobacco-smoke carcinogen activation",
        tissue="lung, nasal mucosa",
    ),
]


# ── Activity Score Reference (per-allele values, CPIC-format) ────────────
# Key = gene, value = list of {allele, value, phenotype, confidence}

ACTIVITY_SCORES: dict[str, list[dict]] = {
    "CYP2D6": [
        {"allele": "*1, *2, *35", "value": 1.0, "phenotype": "Normal Metabolizer", "confidence": "High"},
        {"allele": "*9, *17, *29, *41", "value": 0.5, "phenotype": "NM (lower range)", "confidence": "High"},
        {"allele": "*10", "value": 0.25, "phenotype": "NM (lowest); IM", "confidence": "High"},
        {"allele": "*3, *4, *5, *6, *40", "value": 0.0, "phenotype": "Poor Metabolizer", "confidence": "High"},
        {"allele": "*1x2, *2x2 (dupl.)", "value": 2.0, "phenotype": "Ultrarapid Metabolizer", "confidence": "High"},
    ],
    "CYP2C9": [
        {"allele": "*1", "value": 1.0, "phenotype": "Normal Metabolizer", "confidence": "High"},
        {"allele": "*2", "value": 0.5, "phenotype": "Intermediate Metabolizer", "confidence": "High"},
        {"allele": "*3, *5, *6, *8, *11", "value": 0.0, "phenotype": "IM; PM (AS 0)", "confidence": "High"},
    ],
    "CYP2C19": [
        {"allele": "*1", "value": 1.0, "phenotype": "Normal Metabolizer", "confidence": "High"},
        {"allele": "*17", "value": 1.5, "phenotype": "Rapid Metabolizer", "confidence": "High"},
        {"allele": "*2, *3, *4, *5", "value": 0.0, "phenotype": "Poor Metabolizer", "confidence": "High"},
        {"allele": "*9", "value": 0.5, "phenotype": "Intermediate Metabolizer", "confidence": "High"},
    ],
    "NAT2": [
        {"allele": "*4, *1 (rapid)", "value": 1.0, "phenotype": "Rapid Acetylator", "confidence": "High"},
        {"allele": "*5, *6, *7, *14 (slow)", "value": 0.5, "phenotype": "Intermediate Acetylator", "confidence": "High"},
        {"allele": "*5/*6, *6/*7, etc.", "value": 0.5, "phenotype": "Slow (Poor) Acetylator", "confidence": "High"},
    ],
    "UGT1A1": [
        {"allele": "*1, *36", "value": 1.0, "phenotype": "Normal Metabolizer", "confidence": "High"},
        {"allele": "*28, *6, *37", "value": 0.5, "phenotype": "Intermediate Metabolizer", "confidence": "High"},
        {"allele": "*28/*28, *6/*6", "value": 0.5, "phenotype": "Poor Metabolizer", "confidence": "High"},
    ],
    "CYP1A1": [
        {"allele": "*1 (reference)", "value": 1.0, "phenotype": "Normal activity", "confidence": "Moderate"},
        {"allele": "*2A (MspI, 3'-UTR)", "value": 1.2, "phenotype": "Increased inducibility", "confidence": "Moderate"},
        {"allele": "*2B (MspI + Ile462Val)", "value": 1.3, "phenotype": "High activity (UM-like)", "confidence": "Moderate"},
        {"allele": "*4 (Thr461Val)", "value": 1.2, "phenotype": "Increased activity", "confidence": "Moderate"},
    ],
    "CYP1A2": [
        {"allele": "*1A (reference)", "value": 1.0, "phenotype": "Normal (constitutive)", "confidence": "Moderate"},
        {"allele": "*1F (-163C>A) [induced]", "value": 1.5, "phenotype": "Ultrarapid (induced)", "confidence": "Moderate"},
        {"allele": "*1K (-163A + -729T)", "value": 0.5, "phenotype": "Decreased activity", "confidence": "Moderate"},
        {"allele": "*24 (W84X stop)", "value": 0.0, "phenotype": "IM (one null allele)", "confidence": "Moderate"},
    ],
    "CYP1B1": [
        {"allele": "*1 (reference)", "value": 1.0, "phenotype": "Normal activity", "confidence": "Moderate"},
        {"allele": "Val432 (C allele)", "value": 1.3, "phenotype": "Increased 4-OH-E2 formation", "confidence": "Moderate"},
    ],
    "CYP2A6": [
        {"allele": "*1A, *1B (reference)", "value": 1.0, "phenotype": "Normal Metabolizer", "confidence": "High"},
        {"allele": "*1x2 (gene duplication)", "value": 2.0, "phenotype": "Ultrarapid Metabolizer", "confidence": "High"},
        {"allele": "*9 (-48T>G, TATA box)", "value": 0.5, "phenotype": "Intermediate Metabolizer", "confidence": "High"},
        {"allele": "*2, *4 (null alleles)", "value": 0.0, "phenotype": "Poor Metabolizer", "confidence": "High"},
    ],
    "CYP2E1": [
        {"allele": "c1/c1 (reference; *1A)", "value": 1.0, "phenotype": "Normal activity", "confidence": "Moderate"},
        {"allele": "c2 allele (-1019C>T)", "value": 1.3, "phenotype": "Increased transcription", "confidence": "Moderate"},
        {"allele": "c2/c2 homozygous", "value": 1.3, "phenotype": "High activity", "confidence": "Moderate"},
    ],
    "CYP3A4": [
        {"allele": "*1 (reference)", "value": 1.0, "phenotype": "Normal Metabolizer", "confidence": "High"},
        {"allele": "*22 (intron 6 C>T)", "value": 0.5, "phenotype": "Intermediate Metabolizer", "confidence": "High"},
        {"allele": "*17, *20 (null-like)", "value": 0.0, "phenotype": "IM (one null allele)", "confidence": "Moderate"},
    ],
    "EPHX1": [
        {"allele": "Tyr113 + His139 (ref)", "value": 1.0, "phenotype": "Normal activity", "confidence": "High"},
        {"allele": "113His (exon 3, slow)", "value": 0.5, "phenotype": "Slow activity (~50%)", "confidence": "High"},
        {"allele": "139Arg (exon 4, fast)", "value": 1.25, "phenotype": "Fast activity (~25% increase)", "confidence": "High"},
    ],
    "GSTM1": [
        {"allele": "Non-null (+/+ or +/null)", "value": 1.0, "phenotype": "Present (functional)", "confidence": "High"},
        {"allele": "Null (homozygous deletion)", "value": 0.0, "phenotype": "Absent (no function)", "confidence": "High"},
    ],
    "GSTT1": [
        {"allele": "Non-null (+/+ or +/null)", "value": 1.0, "phenotype": "Present (functional)", "confidence": "High"},
        {"allele": "Null (homozygous deletion)", "value": 0.0, "phenotype": "Absent (no function)", "confidence": "High"},
    ],
    "NQO1": [
        {"allele": "*1 (Pro187, reference)", "value": 1.0, "phenotype": "Normal activity", "confidence": "High"},
        {"allele": "*2 (Pro187Ser, C609T)", "value": 0.25, "phenotype": "Decreased (~25% hetero)", "confidence": "High"},
        {"allele": "*2/*2 (Ser/Ser)", "value": 0.0, "phenotype": "No function (2-4%)", "confidence": "High"},
    ],
    "XPC": [
        {"allele": "Lys939 (reference)", "value": 1.0, "phenotype": "Normal NER capacity", "confidence": "Moderate"},
        {"allele": "Gln939 (rs2228001)", "value": 0.7, "phenotype": "Reduced NER", "confidence": "Moderate"},
    ],
    "OGG1": [
        {"allele": "Ser326 (reference)", "value": 1.0, "phenotype": "Normal 8-oxoG repair", "confidence": "High"},
        {"allele": "Cys326 (rs1052133)", "value": 0.5, "phenotype": "Reduced repair", "confidence": "High"},
    ],
    "MGMT": [
        {"allele": "Unmethylated promoter", "value": 1.0, "phenotype": "Normal O6-MeG repair", "confidence": "High"},
        {"allele": "Partially methylated", "value": 0.5, "phenotype": "Reduced expression", "confidence": "Moderate"},
        {"allele": "Hypermethylated", "value": 0.0, "phenotype": "Silenced (no repair)", "confidence": "High"},
    ],
}


ACTIVITY_SCORE_METADATA: dict[str, dict[str, object]] = {
    "CYP2D6": _activity_score_meta(
        "Guideline-backed pharmacogene",
        "Allele-function and activity-score conventions are aligned to pharmacogene interpretation resources.",
        _clinpgx_ref("CYP2D6"),
        _pharmvar_ref("CYP2D6"),
    ),
    "CYP2C9": _activity_score_meta(
        "Guideline-backed pharmacogene",
        "Core pharmacogene with star-allele interpretation anchored to ClinPGx/PharmVar resources.",
        _clinpgx_ref("CYP2C9"),
        _pharmvar_ref("CYP2C9"),
    ),
    "CYP2C19": _activity_score_meta(
        "Guideline-backed pharmacogene",
        "Core pharmacogene with star-allele interpretation anchored to ClinPGx/PharmVar resources.",
        _clinpgx_ref("CYP2C19"),
        _pharmvar_ref("CYP2C19"),
    ),
    "NAT2": _activity_score_meta(
        "Phenotype-backed pharmacogene",
        "Rapid/intermediate/slow acetylator labels are retained for research-use summarization and should not replace diplotype calling.",
        _clinpgx_ref("NAT2"),
        _ncbi_gene_ref("NAT2"),
        _pubmed_ref(
            "30149019",
            "Expression and genotype-dependent catalytic activity of N-acetyltransferase 2 (NAT2) in human peripheral blood mononuclear cells and its modulation by Sirtuin 1.",
            "Supports NAT2 rapid/intermediate/slow acetylator phenotype interpretation.",
        ),
    ),
    "UGT1A1": _activity_score_meta(
        "Guideline-backed pharmacogene",
        "UGT1A1 star-allele activity groupings are used as pharmacogene-style interpretation aids.",
        _clinpgx_ref("UGT1A1"),
        _ncbi_gene_ref("UGT1A1"),
    ),
    "CYP2A6": _activity_score_meta(
        "Database-backed pharmacogene",
        "Allele-function groupings are supported by pharmacogene resources and smoking-metabolism literature.",
        _clinpgx_ref("CYP2A6"),
        _pharmvar_ref("CYP2A6"),
        _pubmed_ref(
            "29194389",
            "CYP2A6 Genotype and Smoking Behavior in Current Smokers Screened for Lung Cancer.",
            "Supports CYP2A6 metabolizer-group interpretation in nicotine metabolism.",
        ),
    ),
    "CYP3A4": _activity_score_meta(
        "Database-backed pharmacogene",
        "CYP3A4 activity groupings are simplified from pharmacogene resources and should be treated as research-use summaries.",
        _clinpgx_ref("CYP3A4"),
        _pharmvar_ref("CYP3A4"),
        _pubmed_ref(
            "23665933",
            "A common nonfunctional CYP3A4 intron 6 polymorphism significantly affects tacrolimus pharmacokinetics in European-American kidney transplant recipients.",
            "Supports reduced-function interpretation of CYP3A4*22.",
        ),
    ),
    "CYP1A1": _activity_score_meta(
        "Research-use literature-derived",
        "Current values are heuristic activity summaries for carcinogen-metabolism curation, not CPIC-standardized scores.",
        _ncbi_gene_ref("CYP1A1"),
        _pubmed_ref(
            "15647817",
            "Effect of CYP1A1 gene polymorphisms on estrogen metabolism and bone density.",
            "Supports functional interpretation of common CYP1A1 polymorphisms including Ile462Val-containing haplotypes.",
        ),
    ),
    "CYP1A2": _activity_score_meta(
        "Research-use literature-derived",
        "Current values are heuristic inducibility/activity summaries and should be used only for research curation.",
        _ncbi_gene_ref("CYP1A2"),
        _pubmed_ref(
            "16188490",
            "Influence of the genetic polymorphism in the 5'-noncoding region of the CYP1A2 gene on CYP1A2 phenotype and urinary mutagenicity in smokers.",
            "Supports inducibility interpretation for CYP1A2 promoter polymorphisms.",
        ),
    ),
    "CYP1B1": _activity_score_meta(
        "Research-use literature-derived",
        "Current values summarize literature-reported differences in estradiol hydroxylation rather than a standardized clinical score.",
        _ncbi_gene_ref("CYP1B1"),
        _pubmed_ref(
            "10862525",
            "Polymorphisms in P450 CYP1B1 affect the conversion of estradiol to the potentially carcinogenic metabolite 4-hydroxyestradiol.",
            "Supports functional interpretation of CYP1B1 codon 432 variation.",
        ),
    ),
    "CYP2E1": _activity_score_meta(
        "Research-use literature-derived",
        "CYP2E1 functional polymorphism evidence is mixed; these values are retained as tentative research-use annotations.",
        _ncbi_gene_ref("CYP2E1"),
        _pubmed_ref(
            "10886461",
            "Lack of evidence for a role of cytochrome P450 2E1 genetic polymorphisms in the development of different types of cancer.",
            "Provides a review context showing that CYP2E1 polymorphism effects remain debated and should be interpreted cautiously.",
        ),
    ),
    "EPHX1": _activity_score_meta(
        "Research-use literature-derived",
        "EPHX1 activity values reflect long-used low/intermediate/high genotype conventions rather than a formal clinical standard.",
        _ncbi_gene_ref("EPHX1"),
        _pubmed_ref(
            "21445251",
            "Putative EPHX1 enzyme activity is related with risk of lung and upper aerodigestive tract cancers: a comprehensive meta-analysis.",
            "Supports low-activity and high-activity genotype grouping conventions for Tyr113His and His139Arg.",
        ),
    ),
    "GSTM1": _activity_score_meta(
        "Research-use loss-of-function genotype",
        "The GSTM1 null mapping represents a deletion/absence-of-function convention rather than a CPIC activity score.",
        _ncbi_gene_ref("GSTM1"),
        _pubmed_ref(
            "23506349",
            "Utilization of glutathione S-transferase Mu 1- and Theta 1-null mice as animal models for absorption, distribution, metabolism, excretion and toxicity studies.",
            "Supports absent-function interpretation for GSTM1 null status.",
        ),
    ),
    "GSTT1": _activity_score_meta(
        "Research-use loss-of-function genotype",
        "The GSTT1 null mapping represents a deletion/absence-of-function convention rather than a CPIC activity score.",
        _ncbi_gene_ref("GSTT1"),
        _pubmed_ref(
            "23506349",
            "Utilization of glutathione S-transferase Mu 1- and Theta 1-null mice as animal models for absorption, distribution, metabolism, excretion and toxicity studies.",
            "Supports absent-function interpretation for GSTT1 null status.",
        ),
    ),
    "NQO1": _activity_score_meta(
        "Research-use literature-derived",
        "NQO1 values summarize the functional impact of the common Pro187Ser variant for curation purposes.",
        _ncbi_gene_ref("NQO1"),
        _pubmed_ref(
            "23860519",
            "The NQO1 polymorphism C609T (Pro187Ser) and cancer susceptibility: a comprehensive meta-analysis.",
            "Provides consolidated literature context for the reduced-function NQO1*2 allele.",
        ),
    ),
    "XPC": _activity_score_meta(
        "Research-use literature-derived",
        "XPC repair-capacity values are heuristic and should be treated as exploratory annotations rather than clinical scores.",
        _ncbi_gene_ref("XPC"),
        _ctd_ref("XPC", "DNA Repair (NER)"),
    ),
    "OGG1": _activity_score_meta(
        "Research-use literature-derived",
        "OGG1 values summarize the Ser326Cys literature and should be used only for research interpretation.",
        _ncbi_gene_ref("OGG1"),
        _pubmed_ref(
            "41024270",
            "The OGG1 Ser326Cys polymorphism: molecular mechanisms of disease susceptibility and precision medicine applications.",
            "Provides review-level support for functional interpretation of the OGG1 Ser326Cys variant.",
        ),
    ),
    "MGMT": _activity_score_meta(
        "Research-use epigenetic marker",
        "MGMT promoter methylation states are represented as simplified repair-capacity categories for research use.",
        _ncbi_gene_ref("MGMT"),
        _pubmed_ref(
            "20725792",
            "MGMT promoter methylation in malignant gliomas.",
            "Supports the reduced-expression and silencing interpretation of MGMT promoter methylation states.",
        ),
    ),
}


def build_tier1_panel() -> KnowledgeGraph:
    """Return a KnowledgeGraph containing all 13 Tier 1 genes as Enzyme nodes."""
    nodes = [
        Node(id=g["id"], label=g["label"], type=NodeType.ENZYME, tier=1, **{
            k: v for k, v in g.items() if k not in ("id", "label")
        })
        for g in TIER1_GENES
    ]
    return KnowledgeGraph(nodes=nodes, edges=[])


def build_tier2_panel() -> KnowledgeGraph:
    """Return a KnowledgeGraph containing all 15 Tier 2 genes as Enzyme nodes."""
    nodes = [
        Node(id=g["id"], label=g["label"], type=NodeType.ENZYME, tier=2, **{
            k: v for k, v in g.items() if k not in ("id", "label")
        })
        for g in TIER2_GENES
    ]
    return KnowledgeGraph(nodes=nodes, edges=[])


def build_full_panel() -> KnowledgeGraph:
    """Return a KnowledgeGraph with all Tier 1 + Tier 2 genes (28 total)."""
    t1 = build_tier1_panel()
    t2 = build_tier2_panel()
    return KnowledgeGraph(nodes=t1.nodes + t2.nodes, edges=[])


def get_activity_scores(gene: str) -> list[dict] | None:
    """Look up activity score entries for a gene. Returns None if not found."""
    return ACTIVITY_SCORES.get(gene)


def get_activity_score_metadata(gene: str) -> dict[str, object] | None:
    """Return evidence metadata for a gene's activity score table."""
    return ACTIVITY_SCORE_METADATA.get(gene)


def get_activity_score_references(gene: str) -> list[dict] | None:
    """Return supporting references for a gene's activity score table."""
    metadata = get_activity_score_metadata(gene)
    if metadata is None:
        return None
    return metadata.get("references")  # type: ignore[return-value]
