import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase01.guardrails import check_scope, validate_attribution
from phase01.models import Claim, Gap, GapAnalysis, SourceLedger, SourceRecord


def _ledger():
    led = SourceLedger()
    led.add(SourceRecord(cite_id="PMID:1", kind="pubmed", title="t"))
    led.add(SourceRecord(cite_id="K1", kind="fda510k", title="t"))
    return led


def test_scope_accepts_lung_question():
    assert check_scope("unmet needs in lung-nodule CT triage").in_scope


def test_scope_rejects_off_domain():
    assert not check_scope("unmet needs in breast MRI triage").in_scope


def test_scope_rejects_no_anchor():
    assert not check_scope("what software should we build").in_scope


def test_attribution_passes_when_all_cited_and_resolvable():
    analysis = GapAnalysis(
        clinical_question="q", device_context="ctx",
        evidence_summary=[Claim(statement="s", cite_ids=["PMID:1"])],
        grounded_gaps=[Gap(statement="g", severity="high", cite_ids=["K1"])],
    )
    assert validate_attribution(analysis, _ledger()).ok


def test_attribution_rejects_unresolvable_citation():
    analysis = GapAnalysis(
        clinical_question="q", device_context="ctx",
        evidence_summary=[Claim(statement="hallucinated", cite_ids=["PMID:99999"])],
    )
    report = validate_attribution(analysis, _ledger())
    assert not report.ok
    assert any("PMID:99999" in v for v in report.violations)
