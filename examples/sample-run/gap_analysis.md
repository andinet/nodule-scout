# Phase 01 Gap Analysis — APPROVED

> Conceptual ideation aid produced by an autonomous research
> orchestrator. **Not validated SaMD and not clinical guidance.**

**Clinical question:** What are the unmet needs and evidence gaps for an AI lung-nodule detection/triage tool on chest CT?

**Device context:** Software-as-a-Medical-Device (SaMD) AI tool for detection and triage of pulmonary nodules on chest CT (including low-dose screening CT), Phase 01 ideation. The competitive predicate space is active across several FDA product codes (OEB, POK, JAK), and intended use may span detection, malignancy-risk estimation, and follow-up recommendation.

_[PASS] source-attribution: 22 claims / 50 citations, 0 violation(s)_

## Evidence summary (PubMed)
- Externally tested AI models for malignancy classification of lung nodules on chest CT show usable pooled diagnostic accuracy, but a systematic review/meta-analysis highlights heterogeneity across models and external test sets, indicating generalizability is not yet settled. [PMID:42233760]
- In a standardized benchmark (LUNA25), an AI system was compared against radiologists for estimating malignancy risk of indeterminate-size nodules (5-15 mm) on low-dose CT, showing AI can approach radiologist-level risk estimation for solid indeterminate nodules. [PMID:42340186]
- AI radiomics-based tools are being explored to support non-radiologist clinicians (advanced practice providers) in pulmonary nodule risk assessment and management, suggesting a triage/decision-support use case beyond the radiologist reader. [PMID:42358939]
- Emerging models attempt to predict pulmonary nodule growth (a malignancy predictor) from a single CT time point via fusion of radiomics and deep learning, pointing to follow-up-optimization use cases beyond simple detection. [PMID:42306661]
- Uptake of low-dose CT lung cancer screening among eligible high-risk individuals remains low, and multicentre cohorts are still characterizing risk factors, meaning the population an AI triage tool would serve is under-screened and heterogeneous. [PMID:42302275] [PMID:42082236]

## Safety signals (FDA MAUDE)
- Real-world MAUDE data relevant to lung-nodule AI is extremely sparse and noisy: 12 of 15 retrieved records are dental CAD/CAM restoration systems (acronym collision on 'CAD') and are not relevant to this device class; only two records are plausibly relevant. [MAUDE:23888701] [MAUDE:23829153] [MAUDE:22327742] [MAUDE:11648699] [MAUDE:6645328]
- The most relevant MAUDE signal is a computer-assisted diagnostic software for lesions suspicious for cancer reporting software-reliability failure modes (image display error/artifact and the application freezing or failing to launch), which are integration/reliability failures rather than raw model-accuracy failures. [MAUDE:11195257]
- A CT imaging-chain safety event (radiation overexposure) appears in the retrieved records, a reminder that the acquisition context upstream of the AI carries its own patient-safety risks, though it is not attributable to nodule-detection software. [MAUDE:7472705]
- Because the relevant post-market corpus is so small, MAUDE cannot currently be used to characterize the real-world failure-mode distribution for lung-nodule AI; absence of signal here reflects data sparseness and acronym collision, not demonstrated safety. [MAUDE:11195257] [MAUDE:7472705]

## Predicate landscape (FDA 510(k))
- The lung-nodule CAD detection predicate space (product code OEB) is active and recently cleared, including Fujifilm Synapse Lung Nodule AI, Coreline AVIEW Lung Nodule CAD, Infervision InferRead Lung CT.AI, and V5med Lung AI. [K254075] [K251203] [K240554] [K242919]
- Adjacent lung predicates cleared under different product codes indicate intended-use divergence: RevealAI-Lung under POK (malignancy characterization) versus Riverain ClearRead CT CAC, Brainomix 360 e-Lung, and Arineta SpotLight low-dose screening options under JAK. [K251769] [K242188] [K242411] [K250650] [K241200]
- The most recent lung-nodule clearances are dated into 2025-2026, confirming a crowded, fast-moving competitive field that a new entrant must differentiate against on more than baseline detection accuracy. [K254075] [K251203] [K251769]

## Advisory-grounded gaps / unmet needs
- Subsolid (ground-glass and part-solid) nodule performance is a recognized weakness of CAD/AI tools and carries high clinical stakes for indolent adenocarcinoma, yet the strongest current benchmark evidence centers on solid indeterminate nodules (5-15 mm), leaving a validated evidence gap for subsolid disease. _(severity: high)_ [NOTE:subsolid-nodules] [PMID:42340186]
- False-positive burden and automation bias differ sharply between low-prevalence screening and incidental contexts, driving downstream follow-up CTs and biopsies; context-specific false-positive tolerance is not resolved by pooled accuracy metrics that mix populations. _(severity: high)_ [NOTE:false-positive-tolerance] [PMID:42233760]
- Workflow and PACS/worklist integration is treated as make-or-break for adoption and turnaround-time value, and the closest real-world failure signal is a diagnostic-software reliability/display failure rather than a model-accuracy failure, yet integration and reliability are under-evidenced relative to accuracy. _(severity: high)_ [NOTE:workflow-integration] [MAUDE:11195257]
- Detection, malignancy-risk estimation, and follow-up recommendation are three distinct intended uses with escalating regulatory and liability weight, and products blur them; the predicate landscape's split across OEB, POK, and JAK codes confirms this boundary is consequential and easy to overstep. _(severity: high)_ [NOTE:intended-use-boundary] [K251203] [K251769] [K242188]
- External generalizability across sites, scanners, and populations remains heterogeneous in the meta-analytic evidence, while the target screening population is under-screened and demographically variable, leaving a gap in demonstrated real-world transportability. _(severity: medium)_ [PMID:42233760] [PMID:42082236]

## Recommended next steps
- Prioritize a dedicated subsolid/part-solid nodule validation plan (stratified sensitivity and false-positive reporting), since this is the highest-stakes, least-covered performance regime. [NOTE:subsolid-nodules] [PMID:42340186]
- Fix the intended-use boundary early (detection vs malignancy-risk vs follow-up recommendation) and choose the predicate/product-code lane deliberately to bound regulatory and liability exposure. [NOTE:intended-use-boundary] [K251769] [K242188]
- Invest in PACS/worklist integration and software-reliability testing (display integrity, launch/uptime, worklist routing) as a first-class requirement, informed by the observed diagnostic-software failure modes. [NOTE:workflow-integration] [MAUDE:11195257]
- Define context-specific operating points and false-positive thresholds separately for screening (low prevalence) versus incidental use, and design human-factors evaluation of automation bias into the study. [NOTE:false-positive-tolerance] [PMID:42233760]
- Plan multi-site external validation across scanners and under-screened populations to address demonstrated generalizability heterogeneity before pivotal claims. [PMID:42233760] [PMID:42082236]

## Open questions (uncited by design)
- MAUDE for this device class is too sparse and acronym-collided to characterize the true real-world failure-mode distribution for lung-nodule AI; a targeted post-market surveillance strategy (by product code rather than 'CAD' keyword) is needed to close this blind spot.
- Reimbursement and economic-value evidence (does reduced time-to-report or triage translate to payer/health-system value?) was not established by the retrieved sources.
- How is medico-legal liability allocated when the tool issues a follow-up recommendation versus flags detection only?
- What is the subgroup/health-equity performance (by sex, race/ethnicity, comorbidity, scanner vendor) — no retrieved source quantified fairness or subgroup drift?
- What is the appropriate human-AI interaction model (concurrent read, second read, autonomous triage) and its measured effect on reader sensitivity and workload?

## References
- **K240554** — InferRead Lung CT.AI — Infervision Medical Technology Co., Ltd. · cleared 2025-05-16 — https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K240554
- **K241200** — SpotLight/SpotLight Duo with Low Dose Lung Cancer Screening Option — Arineta , Ltd. · cleared 2025-01-13 — https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K241200
- **K242188** — ClearRead CT CAC — Riverain Technologies, Inc. · cleared 2024-12-03 — https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K242188
- **K242411** — Brainomix 360 e-Lung — Brainomix Limited · cleared 2025-02-19 — https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K242411
- **K242919** — V5med Lung AI — V5med, Inc. · cleared 2025-03-27 — https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K242919
- **K250650** — SpotLight / SpotLight Duo with Low Dose Lung Cancer Screening Option — Arineta , Ltd. · cleared 2025-04-15 — https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K250650
- **K251203** — AVIEW Lung Nodule CAD — Coreline Soft Co., Ltd. · cleared 2025-12-03 — https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K251203
- **K251769** — RevealAI-Lung — Precision Medical Ventures, Inc. Dba Revealdx · cleared 2026-01-30 — https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K251769
- **K254075** — Synapse Lung Nodule AI — Fujifilm Corporation · cleared 2026-05-27 — https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K254075
- **MAUDE:11195257** — Computer-Assisted Diagnostic Software For Lesions Suspicious For Cancer — Malfunction · 20210115 — https://api.fda.gov/device/event.json?search=mdr_report_key:11195257
- **MAUDE:11648699** — System, Optical Impression, Computer Assisted Design And Manufacturing (Cad/Cam) Of Dental Restorations — Malfunction · 20210412 — https://api.fda.gov/device/event.json?search=mdr_report_key:11648699
- **MAUDE:22327742** — System, Optical Impression, Computer Assisted Design And Manufacturing (Cad/Cam) Of Dental Restorations — Malfunction · 20250625 — https://api.fda.gov/device/event.json?search=mdr_report_key:22327742
- **MAUDE:23829153** — System, Optical Impression, Computer Assisted Design And Manufacturing (Cad/Cam) Of Dental Restorations — Injury · 20251217 — https://api.fda.gov/device/event.json?search=mdr_report_key:23829153
- **MAUDE:23888701** — System, Optical Impression, Computer Assisted Design And Manufacturing (Cad/Cam) Of Dental Restorations — Malfunction · 20251224 — https://api.fda.gov/device/event.json?search=mdr_report_key:23888701
- **MAUDE:6645328** — System, Optical Impression, Computer Assisted Design And Manufacturing (Cad/Cam) Of Dental Restorations — Malfunction · 20170615 — https://api.fda.gov/device/event.json?search=mdr_report_key:6645328
- **MAUDE:7472705** — System, X-Ray, Tomography, Computed — Injury · 20180427 — https://api.fda.gov/device/event.json?search=mdr_report_key:7472705
- **NOTE:false-positive-tolerance** — False-positive burden and automation bias
- **NOTE:intended-use-boundary** — Intended-use boundary — detection vs malignancy-risk vs follow-up recommendation
- **NOTE:subsolid-nodules** — Subsolid and part-solid nodule performance
- **NOTE:workflow-integration** — PACS/worklist integration and turnaround-time claims
- **PMID:42082236** — Understanding LUng Cancer risk factors and their Impact Assessment (LUCIA): protocol for multicentre observational cohort study — BMJ open 2026 — https://pubmed.ncbi.nlm.nih.gov/42082236/
- **PMID:42233760** — Externally Tested AI Models for Malignancy Classification of Lung Nodules at CT: A Systematic Review and Meta-Analysis — Radiology. Artificial intelligence 2026 — https://pubmed.ncbi.nlm.nih.gov/42233760/
- **PMID:42302275** — Online Intervention on Lung Cancer Screening Among High-Risk Individuals: Pilot Intervention Study — JMIR cancer 2026 — https://pubmed.ncbi.nlm.nih.gov/42302275/
- **PMID:42306661** — Predicting pulmonary nodule growth from a single time point: a fusion model of radiomics and deep learning to optimize follow-up strategies — Journal of thoracic disease 2026 — https://pubmed.ncbi.nlm.nih.gov/42306661/
- **PMID:42340186** — Benchmarking of AI and Radiologists for Indeterminate Lung Nodule Malignancy Risk Estimation on Screening CT: The LUNA25 Challenge — Radiology. Artificial intelligence 2026 — https://pubmed.ncbi.nlm.nih.gov/42340186/
- **PMID:42358939** — Theoretical Clinical Utility of Advanced Practice Provider Use of an Artificial Intelligence Radiomics-based Tool for Pulmonary Nodule Evaluation and Management — CHEST pulmonary 2026 — https://pubmed.ncbi.nlm.nih.gov/42358939/
