"""CLI entrypoint for the Phase 01 lung-nodule research orchestrator.

    python run.py "What are the unmet needs in AI lung-nodule detection/triage on chest CT?"

Flags:
    --agentic     Use the multi-subagent orchestrator (faithful to the blog).
                  Default is the deterministic code-orchestrated sidebar.
    --approve     Promote the draft to a finalized gap_analysis.md without a prompt
                  (models an explicit regulatory sign-off).
    --out DIR     Output directory (default: outputs/).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from phase01.guardrails import check_scope, validate_attribution  # noqa: E402
from phase01.orchestrator import run_agentic, run_deterministic  # noqa: E402
from phase01.render import write_artifact  # noqa: E402

DEFAULT_QUESTION = (
    "What are the unmet needs and evidence gaps for an AI lung-nodule "
    "detection/triage tool on chest CT?"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    ap.add_argument("--agentic", action="store_true", help="Use multi-subagent orchestrator.")
    ap.add_argument("--approve", action="store_true", help="Auto-promote draft to approved.")
    ap.add_argument("--out", default="outputs", help="Output directory.")
    args = ap.parse_args()

    # Guardrail 1: scope constraint, before any API/model spend.
    scope = check_scope(args.question)
    print(f"[scope] {scope.reason}")
    if not scope.in_scope:
        print("Refusing: question is out of the lung-nodule SaMD scope.", file=sys.stderr)
        return 2

    mode = "agentic (multi-subagent)" if args.agentic else "deterministic (code-orchestrated)"
    print(f"[run] mode: {mode}\n[run] question: {args.question}\n")

    runner = run_agentic if args.agentic else run_deterministic
    ctx = asyncio.run(runner(args.question, interactive=False))

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "trace.jsonl").write_text(
        "\n".join(json.dumps(t) for t in ctx.trace) + "\n", encoding="utf-8"
    )
    print(f"[ledger] {len(ctx.ledger)} source records fetched")

    if ctx.submitted is None:
        print("\nNo gap analysis was accepted by the citation guardrail.", file=sys.stderr)
        if ctx.last_violations:
            print("Last violations:", *ctx.last_violations, sep="\n  ", file=sys.stderr)
        return 1

    report = validate_attribution(ctx.submitted, ctx.ledger)
    print(f"[guardrail] {report.summary()}")

    # Always write a DRAFT first (human-in-the-loop).
    md, js = write_artifact(out_dir, ctx.submitted, ctx.ledger, report, approved=False)
    print(f"[draft] {md}\n[draft] {js}")

    # Guardrail 3: human-in-the-loop approval gate.
    approve = args.approve
    if not approve and sys.stdin.isatty():
        approve = input("\n[human-in-the-loop] Finalize this gap analysis? [y/N] ").strip().lower() == "y"
    if approve:
        md, js = write_artifact(out_dir, ctx.submitted, ctx.ledger, report, approved=True)
        print(f"[approved] {md}\n[approved] {js}")
    else:
        print("\nLeft as draft. Re-run with --approve (or answer 'y') to finalize.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
