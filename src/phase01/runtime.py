"""Shared Agent-SDK runtime: the Source Ledger, the in-process tool server, the
guardrail hooks, and the human-in-the-loop permission gate.

Both orchestrators (the faithful multi-subagent one and the deterministic
sidebar) build their tools from here, so the citation guardrail and the ledger
behave identically regardless of how synthesis is driven.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from claude_agent_sdk import (
    HookMatcher,
    PermissionResultAllow,
    PermissionResultDeny,
    create_sdk_mcp_server,
    tool,
)

from .guardrails import validate_attribution
from .models import GapAnalysis, SourceLedger, SourceRecord
from .tools.fda510k import search_510k
from .tools.maude import search_maude
from .tools.pubmed import search_pubmed
from .tools.retrieval import retrieve_notes

# Domain anchors reused by the PreToolUse scope hook.
_ANCHORS = ("lung", "pulmonary", "nodule", "chest", "ct", "thoracic", "cancer", "radiolog")


@dataclass
class RunContext:
    """Per-run state that in-process tools read and write."""

    question: str
    ledger: SourceLedger = field(default_factory=SourceLedger)
    submitted: GapAnalysis | None = None
    attribution_ok: bool = False
    last_violations: list[str] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)


def _summarize(records: list[SourceRecord], kind: str) -> str:
    if not records:
        return f"No {kind} records matched. Report this as an absence, do not invent findings."
    lines = [f"{len(records)} {kind} record(s) fetched (each is a citable source):"]
    for r in records:
        extra = ""
        p = r.payload
        if r.kind == "pubmed":
            extra = f" [{p.get('journal','')} {p.get('year','')}] {p.get('abstract_snippet','')[:220]}"
        elif r.kind == "fda510k":
            extra = f" [{p.get('applicant','')}, {p.get('decision_date','')}, code {p.get('product_code','')}]"
        elif r.kind == "maude":
            extra = f" [{p.get('event_type','')}; problems={p.get('product_problems','')}]"
        elif r.kind == "advisory_note":
            extra = f" {p.get('text','')[:260]}"
        lines.append(f"- {r.cite_id}: {r.title}{extra}")
    return "\n".join(lines)


def build_tool_server(ctx: RunContext):
    """Create the in-process MCP server whose tools write to ``ctx.ledger``."""

    @tool("pubmed_search",
          "Search recent PubMed literature on AI lung-nodule detection/triage on chest CT. "
          "Returns citable PMID records.",
          {"focus": str})
    async def pubmed_search(args):
        recs = search_pubmed(focus=args.get("focus") or "triage OR malignancy risk")
        ctx.ledger.add_all(recs)
        ctx.trace.append({"tool": "pubmed_search", "n": len(recs), "ids": [r.cite_id for r in recs]})
        return {"content": [{"type": "text", "text": _summarize(recs, "PubMed")}]}

    @tool("maude_query",
          "Query the FDA MAUDE adverse-event database for reported failures in "
          "computer-aided detection / lung-imaging devices. Returns citable MAUDE records.",
          {"note": str})
    async def maude_query(args):
        recs = search_maude()
        ctx.ledger.add_all(recs)
        ctx.trace.append({"tool": "maude_query", "n": len(recs), "ids": [r.cite_id for r in recs]})
        return {"content": [{"type": "text", "text": _summarize(recs, "MAUDE")}]}

    @tool("fivetenk_summary",
          "Retrieve FDA 510(k) predicate device clearances for lung-nodule / radiology "
          "CAD software. Returns citable K-number records.",
          {"note": str})
    async def fivetenk_summary(args):
        recs = search_510k()
        ctx.ledger.add_all(recs)
        ctx.trace.append({"tool": "fivetenk_summary", "n": len(recs), "ids": [r.cite_id for r in recs]})
        return {"content": [{"type": "text", "text": _summarize(recs, "510(k)")}]}

    @tool("search_advisory_notes",
          "Retrieve the internal clinical advisory-board notes most relevant to a query "
          "(synthetic sample corpus). Returns citable NOTE records for grounding gaps.",
          {"query": str})
    async def search_advisory_notes(args):
        recs = retrieve_notes(args.get("query") or ctx.question, k=4)
        ctx.ledger.add_all(recs)
        ctx.trace.append({"tool": "search_advisory_notes", "n": len(recs), "ids": [r.cite_id for r in recs]})
        return {"content": [{"type": "text", "text": _summarize(recs, "advisory-note")}]}

    @tool("submit_gap_analysis",
          "Submit the final structured gap analysis. Every claim MUST cite source ids "
          "that appeared in tool results this run. Rejected if any citation is unresolvable.",
          {"gap_analysis_json": str})
    async def submit_gap_analysis(args):
        raw = args.get("gap_analysis_json") or "{}"
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            analysis = GapAnalysis.model_validate(data)
        except Exception as exc:  # schema/JSON error -> tell the model to fix it
            return {"content": [{"type": "text", "text": f"REJECTED: invalid gap_analysis: {exc}"}],
                    "is_error": True}
        report = validate_attribution(analysis, ctx.ledger)
        ctx.trace.append({"tool": "submit_gap_analysis", "attribution_ok": report.ok,
                          "violations": report.violations})
        if not report.ok:
            ctx.last_violations = report.violations
            msg = "REJECTED by citation guardrail. Fix these and resubmit:\n" + "\n".join(
                f"- {v}" for v in report.violations
            )
            return {"content": [{"type": "text", "text": msg}], "is_error": True}
        ctx.submitted = analysis
        ctx.attribution_ok = True
        return {"content": [{"type": "text", "text":
                f"ACCEPTED: {report.summary()}. Draft written for human approval."}]}

    server = create_sdk_mcp_server(name="research-tools", version="0.1.0",
                                   tools=[pubmed_search, maude_query, fivetenk_summary,
                                          search_advisory_notes, submit_gap_analysis])
    return server


def domain_guard_hook():
    """PreToolUse hook: reject a research query that drifts off the lung-nodule domain."""

    async def _hook(input_data, tool_use_id, context):
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {}) or {}
        # Only police the free-text query fields of retrieval tools.
        query_text = " ".join(
            str(tool_input.get(k, "")) for k in ("focus", "query", "note")
        ).lower()
        if query_text.strip() and not any(a in query_text for a in _ANCHORS):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Scope guard: query {query_text!r} lacks a lung-nodule anchor "
                        "(lung/pulmonary/nodule/chest CT). Stay on the target SaMD domain."
                    ),
                }
            }
        return {}

    return HookMatcher(matcher=None, hooks=[_hook])


def human_gate(interactive: bool):
    """can_use_tool callback: intercept submit_gap_analysis for the HITL approval gate.

    Non-interactive (the default here): always allow, then run.py writes a *draft*
    that a human must promote. Interactive: prompt y/N before accepting.
    """

    async def _gate(tool_name, tool_input, context):
        if tool_name != "mcp__research-tools__submit_gap_analysis":
            return PermissionResultAllow()
        if not interactive:
            return PermissionResultAllow()
        ans = input("\n[human-in-the-loop] Accept submitted gap analysis? [y/N] ").strip().lower()
        if ans == "y":
            return PermissionResultAllow()
        return PermissionResultDeny(message="Human reviewer declined; revise and resubmit.")

    return _gate
