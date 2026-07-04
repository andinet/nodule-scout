"""Typed data model for the Phase 01 research orchestrator.

Two ideas carry the whole design:

1.  ``SourceRecord`` / ``SourceLedger`` — every record any tool fetches is
    appended to a run-scoped ledger under a stable ``cite_id``
    (``PMID:39123456``, ``K233456``, ``MAUDE:...``, ``NOTE:triage#2``). The
    ledger is the ground truth of "what was actually retrieved this run".

2.  ``GapAnalysis`` — the structured deliverable. Every ``Claim`` MUST carry at
    least one ``cite_id``; a deterministic validator (see ``guardrails.py``)
    later rejects any claim whose ids don't resolve in the ledger. That check is
    the concrete mechanism behind the blog's "every claim cites a verifiable
    source" guardrail.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SourceKind = Literal["pubmed", "maude", "fda510k", "advisory_note"]


class SourceRecord(BaseModel):
    """One retrieved record, stored in the run's Source Ledger."""

    cite_id: str = Field(..., description="Stable citation id, e.g. 'PMID:39123456'.")
    kind: SourceKind
    title: str
    url: str | None = None
    payload: dict = Field(default_factory=dict, description="Raw structured fields.")


class SourceLedger(BaseModel):
    """Append-only, de-duplicated collection of everything fetched this run."""

    records: dict[str, SourceRecord] = Field(default_factory=dict)

    def add(self, record: SourceRecord) -> None:
        self.records.setdefault(record.cite_id, record)

    def add_all(self, records: list[SourceRecord]) -> None:
        for r in records:
            self.add(r)

    def __contains__(self, cite_id: str) -> bool:
        return cite_id in self.records

    def __len__(self) -> int:
        return len(self.records)

    def by_kind(self, kind: SourceKind) -> list[SourceRecord]:
        return [r for r in self.records.values() if r.kind == kind]


# --- The structured gap-analysis deliverable ------------------------------


class Claim(BaseModel):
    """A single factual statement. Must be traceable to >=1 fetched record."""

    statement: str
    cite_ids: list[str] = Field(
        ..., min_length=1,
        description="One or more cite_ids that appeared in a tool result this run.",
    )
    confidence: Literal["high", "medium", "low"] = "medium"


class Gap(BaseModel):
    statement: str
    severity: Literal["high", "medium", "low"]
    cite_ids: list[str] = Field(..., min_length=1)


class GapAnalysis(BaseModel):
    """The Phase 01 artifact. Sections map to the blog's sub-agents + RAG step."""

    clinical_question: str
    device_context: str = Field(
        ..., description="One paragraph framing the target SaMD (lung-nodule CT triage)."
    )
    evidence_summary: list[Claim] = Field(
        default_factory=list, description="From PubMed literature."
    )
    safety_signals: list[Claim] = Field(
        default_factory=list, description="From FDA MAUDE adverse events."
    )
    predicate_landscape: list[Claim] = Field(
        default_factory=list, description="From FDA 510(k) clearances."
    )
    grounded_gaps: list[Gap] = Field(
        default_factory=list,
        description="Unmet needs, grounded in the internal advisory notes.",
    )
    recommended_next_steps: list[Claim] = Field(default_factory=list)
    open_questions: list[str] = Field(
        default_factory=list,
        description="Uncited by design: things the evidence did not answer.",
    )

    def all_claims(self) -> list[Claim | Gap]:
        return [
            *self.evidence_summary,
            *self.safety_signals,
            *self.predicate_landscape,
            *self.grounded_gaps,
            *self.recommended_next_steps,
        ]
