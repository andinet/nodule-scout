"""Live network smoke tests — each public API should return >=1 record.

Run with:  PYTHONPATH=src python -m pytest tests/test_tools_smoke.py
Skipped assumptions: network available; APIs up. These hit real endpoints.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase01.tools.fda510k import search_510k
from phase01.tools.maude import search_maude
from phase01.tools.pubmed import search_pubmed
from phase01.tools.retrieval import retrieve_notes


def test_pubmed_returns_records():
    recs = search_pubmed(retmax=3)
    assert recs and all(r.cite_id.startswith("PMID:") for r in recs)


def test_510k_returns_records():
    recs = search_510k(limit=3)
    assert recs and all(r.kind == "fda510k" for r in recs)


def test_maude_query_runs():
    # MAUDE is deliberately sparse for these devices; assert it returns cleanly.
    recs = search_maude(limit=3)
    assert isinstance(recs, list)


def test_advisory_retrieval_grounds_on_notes():
    recs = retrieve_notes("false positive burden in screening", k=3)
    assert recs and all(r.cite_id.startswith("NOTE:") for r in recs)
