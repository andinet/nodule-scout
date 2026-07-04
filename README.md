# nodule-scout

A small, **runnable** research-orchestrator agent that helps scope a medical-AI
product during early ideation. Given a broad clinical question, it dispatches
specialized tool-calling sub-agents at **real public FDA/NIH APIs**, grounds the
results in internal clinical-advisory notes, and emits a structured,
**fully-cited gap-analysis** — refusing to ship any claim it can't trace back to
a fetched source.

It is specialized to **AI lung-nodule detection/triage on chest CT** (predicate
space: Fujifilm Synapse Lung Nodule AI, Coreline AVIEW, Riverain ClearRead CT,
RevealAI-Lung, Infervision, …). It's the companion code for a blog post on
agentic AI in the Software-as-a-Medical-Device (SaMD) lifecycle —
[*Agentic AI is coming to the SaMD lifecycle*](https://blog.andinet.dev/agentic-ai-is-coming-to-the-samd-lifecycle).

> ⚠️ This is a conceptual ideation aid. It is **not validated SaMD** and produces
> **no clinical guidance**. The advisory-notes corpus under `data/` is synthetic.

## What it does

```
 clinical question ─▶ ORCHESTRATOR (Claude Opus 4.8)
                        decompose → dispatch → ground → synthesize
        ┌───────────────────┼────────────────────┐
   pubmed-researcher   maude-analyst      predicate-analyst      + RAG over
   (PubMed E-utils)   (openFDA MAUDE)    (openFDA 510(k))        advisory notes
        └─────────── Source Ledger (every fetched record) ──────┘
                                │
                 guardrails: scope · citation · human-in-the-loop
                                │
                   outputs/gap_analysis.md + .json + trace.jsonl
```

- **Three real data sources, no API key required** — PubMed E-utilities, openFDA
  MAUDE (device adverse events), openFDA 510(k) (predicate clearances).
- **Source Ledger** — every record any tool fetches is stored under a stable
  `cite_id` (`PMID:########`, `K######`, `MAUDE:########`, `NOTE:<id>`).
- **Citation guardrail** — the gap analysis is produced through a
  `submit_gap_analysis` tool; a *deterministic* validator rejects the submission
  if any claim carries no citation or cites an id absent from the ledger. This is
  how "every claim cites a verifiable source" is enforced — not by trusting the
  model.
- **Scope guard** — an off-domain question (e.g. `breast MRI triage`) is refused
  before any spend.
- **Human-in-the-loop** — the run writes a `*.draft` first; nothing is finalized
  without explicit approval (`--approve`).

Built on the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
(`claude-agent-sdk`), authenticated through the logged-in `claude` CLI (Claude
Code) — no separate `ANTHROPIC_API_KEY` required.

See a real, committed run in **[`examples/sample-run/`](examples/sample-run/)**
(46 source records, 22 claims, 50 citations, 0 guardrail violations).

## Quickstart

```bash
pip install -e .            # or: pip install claude-agent-sdk httpx pydantic rank-bm25 python-frontmatter
cp .env.example .env        # optional — API keys only raise rate limits

# Deterministic, code-orchestrated run (reproducible; recommended):
python run.py "What are the unmet needs for an AI lung-nodule triage tool on chest CT?" --approve

# Faithful multi-subagent run (Task fan-out to PubMed/MAUDE/510k sub-agents):
python run.py --agentic --approve
```

Outputs land in `outputs/`: `gap_analysis.md`, `gap_analysis.json` (analysis +
full evidence index + attribution report), and `trace.jsonl`.

## Two orchestration modes

| | `run_deterministic` (default) | `run_agentic` (`--agentic`) |
|---|---|---|
| Retrieval | code calls the 4 tools directly | orchestrator dispatches 3 sub-agents via the **Task** tool |
| Reproducible | yes | no (model-driven fan-out) |
| Stability | robust | experimental¹ |

Both share the ledger, tools, guardrails, and HITL gate in
[`src/phase01/runtime.py`](src/phase01/runtime.py).

> ¹ `--agentic` drives the Agent SDK's `Task` sub-agent dispatch, which is
> model-driven and, combined with hooks under a non-interactive process on some
> platforms, can occasionally hit an SDK↔CLI transport error. The
> **deterministic** mode is the recommended, reproducible path.

## Layout

```
src/phase01/
  models.py       SourceRecord / SourceLedger / GapAnalysis (Claim requires >=1 cite)
  tools/          pubmed.py · maude.py · fda510k.py · retrieval.py (BM25) · http.py
  runtime.py      in-process SDK tools, Source Ledger, scope hook, HITL gate
  orchestrator.py run_agentic (subagents) + run_deterministic
  guardrails.py   check_scope · validate_attribution (the citation gate)
  render.py       markdown + JSON artifact with a References section
data/advisory_notes/   synthetic advisory-board corpus (RAG source)
examples/sample-run/   a real, committed gap analysis
run.py            CLI entrypoint + human-in-the-loop
tests/            guardrail unit tests + live-API smoke tests
```

## Tests

```bash
PYTHONPATH=src python -m pytest tests/ -q
```

Covers: an injected uncited/unresolvable citation is rejected, an off-domain
question is flagged, and each live API returns records.

## Data sources

- PubMed E-utilities — <https://www.ncbi.nlm.nih.gov/books/NBK25501/>
- openFDA device adverse events (MAUDE) — <https://open.fda.gov/apis/device/event/>
- openFDA device 510(k) — <https://open.fda.gov/apis/device/510k/>

## License

MIT — see [LICENSE](LICENSE).
