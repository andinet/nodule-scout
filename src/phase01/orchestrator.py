"""The research orchestrator — the pattern the blog's Phase 01 describes.

``run_agentic`` is faithful to the blog: an orchestrator model decomposes the
clinical question and dispatches to three tool-restricted sub-agents (PubMed,
MAUDE, 510(k)) via the Task tool, grounds the result in the advisory notes, and
submits a structured gap analysis through the citation guardrail.

``run_deterministic`` is the code-orchestrated sidebar: it calls the four
retrieval tools directly (reproducible, cheap) and makes a single synthesis call.
Both share the ledger, tools, hooks, and HITL gate from ``runtime.py``.
"""

from __future__ import annotations

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query

from .models import GapAnalysis
from .runtime import RunContext, build_tool_server, domain_guard_hook, human_gate
from .tools.fda510k import search_510k
from .tools.maude import search_maude
from .tools.pubmed import search_pubmed
from .tools.retrieval import retrieve_notes

MODEL = "claude-opus-4-8"
SUBAGENT_MODEL = "claude-sonnet-5"

T = "mcp__research-tools__"

_SUBMISSION_SPEC = (
    "Then call submit_gap_analysis ONCE with gap_analysis_json set to a JSON object "
    "matching this schema: {clinical_question, device_context, evidence_summary:[{statement, "
    "cite_ids:[...], confidence}], safety_signals:[...same...], predicate_landscape:[...same...], "
    "grounded_gaps:[{statement, severity, cite_ids:[...]}], recommended_next_steps:[...same as "
    "evidence_summary...], open_questions:[str,...]}. "
    "EVERY cite_id in every claim MUST be an id that appeared verbatim in a tool result this run "
    "(e.g. PMID:########, K######, MAUDE:########, NOTE:<id>). If you cannot cite a statement, "
    "move it to open_questions instead of inventing a citation."
)

ORCHESTRATOR_PROMPT = (
    "You are a Phase 01 (Ideation & User Needs) research orchestrator for a Software-as-a-"
    "Medical-Device team building an AI lung-nodule detection/triage tool for chest CT. "
    "Decompose the clinical question into: (1) recent clinical evidence, (2) real-world "
    "software-failure signals, (3) the predicate device landscape, (4) internal clinical "
    "concerns. Dispatch (1) to the pubmed-researcher sub-agent, (2) to the maude-analyst, "
    "(3) to the predicate-analyst — use the Task tool. For (4) call search_advisory_notes "
    "yourself. MAUDE data for these devices is sparse and noisy (the 'CAD' acronym collides "
    "with dental CAD/CAM); filter to relevant records and report sparseness honestly. "
    "You MUST gather evidence from ALL FOUR sources (literature, MAUDE, predicates, "
    "advisory notes) before submitting — do not ground the analysis on advisory notes "
    "alone. "
    + _SUBMISSION_SPEC
)


def _subagents() -> dict[str, AgentDefinition]:
    return {
        "pubmed-researcher": AgentDefinition(
            description="Retrieves recent clinical literature on AI lung-nodule CT triage via PubMed.",
            prompt="Call pubmed_search with a focused query, then report the returned PMID records "
                   "and their key findings. Cite PMIDs exactly as returned.",
            tools=[f"{T}pubmed_search"], model=SUBAGENT_MODEL),
        "maude-analyst": AgentDefinition(
            description="Mines FDA MAUDE for software failures in CAD / lung-imaging devices.",
            prompt="Call maude_query, then report only records relevant to imaging/CAD software "
                   "failures, citing MAUDE ids exactly. Note if the set is sparse or noisy.",
            tools=[f"{T}maude_query"], model=SUBAGENT_MODEL),
        "predicate-analyst": AgentDefinition(
            description="Pulls FDA 510(k) predicate clearances for lung-nodule / radiology CAD.",
            prompt="Call fivetenk_summary, then report the predicate clearances (K-number, "
                   "applicant, product code, date), citing K-numbers exactly.",
            tools=[f"{T}fivetenk_summary"], model=SUBAGENT_MODEL),
    }


def _options(ctx: RunContext, interactive: bool, *, allowed: list[str],
             agents: dict | None) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        model=MODEL,
        system_prompt=ORCHESTRATOR_PROMPT,
        setting_sources=[],  # don't load ambient project settings
        mcp_servers={"research-tools": build_tool_server(ctx)},
        allowed_tools=allowed,
        agents=agents,
        hooks={"PreToolUse": [domain_guard_hook()]},
        # can_use_tool requires streaming input; only wire the SDK permission
        # gate in interactive mode. Non-interactive runs use run.py's draft->approve gate.
        can_use_tool=human_gate(interactive) if interactive else None,
        max_turns=40,
    )


async def _prompt_stream(text: str):
    yield {"type": "user", "message": {"role": "user", "content": text}}


async def _drain(prompt: str, options: ClaudeAgentOptions, ctx: RunContext,
                 *, interactive: bool = False) -> RunContext:
    prompt_arg = _prompt_stream(prompt) if interactive else prompt
    async for _msg in query(prompt=prompt_arg, options=options):
        pass  # tool side-effects populate ctx.ledger / ctx.submitted / ctx.trace
    return ctx


async def run_agentic(question: str, *, interactive: bool = False) -> RunContext:
    ctx = RunContext(question=question)
    # The retrieval tools are allowed at top level too, so a sub-agent invoked via
    # Task can call them (and so the orchestrator gathers complete evidence even if
    # it opts to call a tool directly rather than delegating).
    allowed = [
        "Task",
        f"{T}pubmed_search", f"{T}maude_query", f"{T}fivetenk_summary",
        f"{T}search_advisory_notes", f"{T}submit_gap_analysis",
    ]
    options = _options(ctx, interactive, allowed=allowed, agents=_subagents())
    prompt = f"Clinical question: {question}\n\nProduce the Phase 01 gap analysis."
    return await _drain(prompt, options, ctx, interactive=interactive)


async def run_deterministic(question: str, *, interactive: bool = False) -> RunContext:
    """Code-orchestrated: fetch all evidence directly, then one synthesis call."""

    ctx = RunContext(question=question)
    ctx.ledger.add_all(search_pubmed())
    ctx.ledger.add_all(search_maude())
    ctx.ledger.add_all(search_510k())
    ctx.ledger.add_all(retrieve_notes(question, k=4))
    for r in ctx.ledger.records.values():
        ctx.trace.append({"prefetched": r.cite_id, "kind": r.kind})

    # A compact evidence digest the model synthesizes from (no re-fetching).
    from .runtime import _summarize
    digest = "\n\n".join(
        _summarize(ctx.ledger.by_kind(k), label)
        for k, label in (("pubmed", "PubMed"), ("maude", "MAUDE"),
                         ("fda510k", "510(k)"), ("advisory_note", "advisory-note"))
    )
    allowed = [f"{T}submit_gap_analysis"]
    options = _options(ctx, interactive, allowed=allowed, agents=None)
    prompt = (
        f"Clinical question: {question}\n\nEvidence already retrieved this run "
        f"(cite these ids only):\n\n{digest}\n\nSynthesize the Phase 01 gap analysis."
    )
    return await _drain(prompt, options, ctx, interactive=interactive)
