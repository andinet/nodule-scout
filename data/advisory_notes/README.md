# Synthetic clinical advisory-board notes — NOT REAL CLINICAL GUIDANCE

Every file in this directory is a **synthetic sample** written for this demo. It
is *not* real advisory-board output and must not be used as clinical guidance.
Its only purpose is to make the "RAG over internal advisory notes" step of the
Phase 01 orchestrator concrete and reproducible.

Each note has YAML front-matter (`id`, `date`, `topic`) and short prose. The
retrieval layer (`src/phase01/tools/retrieval.py`) indexes these with BM25 and
exposes the top matches as a citeable source class (`NOTE:<id>`), so
advisory-grounded gaps flow through the same citation guardrail as PubMed,
MAUDE, and 510(k) records.
