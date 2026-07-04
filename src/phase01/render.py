"""Render a validated GapAnalysis to markdown + JSON, with a References section.

Each claim is printed with its citation ids in brackets; every id resolves to a
numbered reference built from the Source Ledger, so a reader can click through to
the real PubMed / openFDA record.
"""

from __future__ import annotations

import json
from pathlib import Path

from .guardrails import AttributionReport
from .models import Claim, Gap, GapAnalysis, SourceLedger


def _cites(item: Claim | Gap) -> str:
    return " ".join(f"[{c}]" for c in item.cite_ids)


def _ref_line(cite_id: str, ledger: SourceLedger) -> str:
    rec = ledger.records.get(cite_id)
    if rec is None:
        return f"- `{cite_id}` — (not in ledger)"
    bits = [f"**{cite_id}**", rec.title or "(untitled)"]
    p = rec.payload
    if rec.kind == "pubmed":
        bits.append(f"{p.get('journal', '')} {p.get('year', '')}".strip())
    elif rec.kind == "fda510k":
        bits.append(f"{p.get('applicant', '')} · cleared {p.get('decision_date', '')}".strip(" ·"))
    elif rec.kind == "maude":
        bits.append(f"{p.get('event_type', '')} · {p.get('date_received', '')}".strip(" ·"))
    line = " — ".join(b for b in bits if b)
    if rec.url:
        line += f" — {rec.url}"
    return f"- {line}"


def render_markdown(
    analysis: GapAnalysis,
    ledger: SourceLedger,
    attribution: AttributionReport,
    *,
    approved: bool,
) -> str:
    L: list[str] = []
    banner = "APPROVED" if approved else "DRAFT — awaiting human approval"
    L.append(f"# Phase 01 Gap Analysis — {banner}")
    L.append("")
    L.append("> Conceptual ideation aid produced by an autonomous research")
    L.append("> orchestrator. **Not validated SaMD and not clinical guidance.**")
    L.append("")
    L.append(f"**Clinical question:** {analysis.clinical_question}")
    L.append("")
    L.append(f"**Device context:** {analysis.device_context}")
    L.append("")
    L.append(f"_{attribution.summary()}_")
    L.append("")

    def section(title: str, items: list) -> None:
        L.append(f"## {title}")
        if not items:
            L.append("")
            L.append("_No records matched — reported as an absence, not inferred._")
            L.append("")
            return
        for it in items:
            sev = f" _(severity: {it.severity})_" if isinstance(it, Gap) else ""
            L.append(f"- {it.statement}{sev} {_cites(it)}")
        L.append("")

    section("Evidence summary (PubMed)", analysis.evidence_summary)
    section("Safety signals (FDA MAUDE)", analysis.safety_signals)
    section("Predicate landscape (FDA 510(k))", analysis.predicate_landscape)
    section("Advisory-grounded gaps / unmet needs", analysis.grounded_gaps)
    section("Recommended next steps", analysis.recommended_next_steps)

    if analysis.open_questions:
        L.append("## Open questions (uncited by design)")
        for q in analysis.open_questions:
            L.append(f"- {q}")
        L.append("")

    # References — only ids actually cited in the artifact.
    cited_ids = sorted({c for it in analysis.all_claims() for c in it.cite_ids})
    L.append("## References")
    for cid in cited_ids:
        L.append(_ref_line(cid, ledger))
    L.append("")
    return "\n".join(L)


def write_artifact(
    out_dir: Path,
    analysis: GapAnalysis,
    ledger: SourceLedger,
    attribution: AttributionReport,
    *,
    approved: bool,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "gap_analysis" if approved else "gap_analysis.draft"
    md_path = out_dir / f"{stem}.md"
    json_path = out_dir / f"{stem}.json"
    md_path.write_text(
        render_markdown(analysis, ledger, attribution, approved=approved),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(
            {
                "analysis": analysis.model_dump(),
                "evidence_index": {k: v.model_dump() for k, v in ledger.records.items()},
                "attribution": {
                    "ok": attribution.ok,
                    "n_claims": attribution.n_claims,
                    "n_citations": attribution.n_citations,
                    "violations": attribution.violations,
                },
                "approved": approved,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return md_path, json_path
