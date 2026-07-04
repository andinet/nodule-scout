"""RAG skill: BM25 retrieval over the synthetic advisory-notes corpus.

Deliberately lightweight — no vector DB. The corpus is ~7 short markdown notes;
lexical overlap with clinical query terms is high, and BM25 is deterministic and
explainable (both desirable for a demo about *grounding* and *traceability*).

The key move: each retrieved chunk becomes a citeable ``SourceRecord``
(``NOTE:<id>``), so advisory-grounded gaps pass through the exact same citation
guardrail as PubMed / MAUDE / 510(k) records.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import frontmatter
from rank_bm25 import BM25Okapi

from ..models import SourceRecord

NOTES_DIR = Path(__file__).resolve().parents[3] / "data" / "advisory_notes"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


@lru_cache(maxsize=1)
def _load_index() -> tuple[BM25Okapi, list[SourceRecord]]:
    records: list[SourceRecord] = []
    corpus_tokens: list[list[str]] = []
    for path in sorted(NOTES_DIR.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        post = frontmatter.load(path)
        note_id = post.get("id", path.stem)
        body = post.content.strip()
        records.append(
            SourceRecord(
                cite_id=f"NOTE:{note_id}",
                kind="advisory_note",
                title=str(post.get("topic", note_id)),
                url=None,
                payload={"date": str(post.get("date", "")), "text": body},
            )
        )
        corpus_tokens.append(_tokenize(f"{post.get('topic', '')} {body}"))
    return BM25Okapi(corpus_tokens), records


def retrieve_notes(query: str, k: int = 4) -> list[SourceRecord]:
    """Return the top-k advisory notes most relevant to ``query`` (BM25)."""

    bm25, records = _load_index()
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(zip(scores, records), key=lambda x: x[0], reverse=True)
    return [rec for score, rec in ranked[:k] if score > 0]
