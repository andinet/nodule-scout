"""Guardrails: the load-bearing part of the demo.

Three layers, mirroring the blog's Phase 01 guardrails:

1.  ``check_scope``     — scope constraint (reject off-domain questions).
2.  ``validate_attribution`` — deterministic source-attribution / anti-
    hallucination gate. Does NOT trust the model: every claim's cite_ids must
    resolve in the run's Source Ledger, and every finding must carry >=1 cite.
3.  The human-in-the-loop approval gate lives in ``run.py`` (draft -> approved).
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import GapAnalysis, SourceLedger

# Domain anchors for the lung-nodule-CT SaMD scope.
ANCHORS = (
    "lung", "pulmonary", "nodule", "chest ct", "low-dose ct", "ldct",
    "lung-rads", "thoracic", "chest radiograph", "lung cancer",
)
# A few obviously off-domain terms that should trip the scope guard.
OFF_DOMAIN = ("mammograph", "breast", "sepsis", "diabetic retinopathy", "stroke", "ecg")


@dataclass
class ScopeVerdict:
    in_scope: bool
    reason: str


def check_scope(question: str) -> ScopeVerdict:
    """Require >=1 lung-nodule anchor term; flag clearly off-domain drift."""

    q = question.lower()
    hits = [a for a in ANCHORS if a in q]
    off = [t for t in OFF_DOMAIN if t in q]
    if off and not hits:
        return ScopeVerdict(False, f"Off-domain terms {off} with no lung-nodule anchor.")
    if not hits:
        return ScopeVerdict(
            False,
            "No lung-nodule anchor term (lung/pulmonary/nodule/chest CT/Lung-RADS) found.",
        )
    return ScopeVerdict(True, f"In scope; matched anchors: {hits}.")


@dataclass
class AttributionReport:
    ok: bool
    violations: list[str]
    n_claims: int
    n_citations: int

    def summary(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        return (
            f"[{status}] source-attribution: {self.n_claims} claims / "
            f"{self.n_citations} citations, {len(self.violations)} violation(s)"
        )


def validate_attribution(analysis: GapAnalysis, ledger: SourceLedger) -> AttributionReport:
    """Every claim must (a) carry >=1 cite_id and (b) resolve in the ledger.

    This is the concrete enforcement of "every claim cites a verifiable source":
    it runs on the produced artifact, deterministically, and does not ask the
    model to self-certify.
    """

    violations: list[str] = []
    n_claims = 0
    n_citations = 0
    for claim in analysis.all_claims():
        n_claims += 1
        cites = getattr(claim, "cite_ids", [])
        if not cites:
            violations.append(f"Uncited claim: {claim.statement[:80]!r}")
            continue
        for cid in cites:
            n_citations += 1
            if cid not in ledger:
                violations.append(
                    f"Unresolvable citation {cid!r} in claim: {claim.statement[:60]!r}"
                )
    return AttributionReport(
        ok=not violations,
        violations=violations,
        n_claims=n_claims,
        n_citations=n_citations,
    )
