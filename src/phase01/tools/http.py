"""Shared HTTP helper: modest timeouts, light retry/backoff, optional API keys.

Every data source used here (PubMed E-utilities, openFDA MAUDE, openFDA 510k) is
a free public API. API keys are optional and only raise rate limits.
"""

from __future__ import annotations

import os
import time

import httpx

USER_AGENT = "phase01-lung-nodule-orchestrator/0.1 (SaMD ideation demo)"


def ncbi_api_key() -> str | None:
    return os.environ.get("NCBI_API_KEY") or None


def openfda_api_key() -> str | None:
    return os.environ.get("OPENFDA_API_KEY") or None


def get_json(url: str, params: dict, *, retries: int = 3, backoff: float = 0.6) -> dict:
    """GET ``url`` and return parsed JSON.

    openFDA returns HTTP 404 with an ``{"error": {"code": "NOT_FOUND"}}`` body
    when a query matches nothing — that is a legitimate "no results", not a
    failure, so we surface it as an empty-but-valid payload rather than raising.
    """

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = httpx.get(
                url, params=params, timeout=20.0,
                headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code == 404:
                return {"results": [], "meta": {"results": {"total": 0}}}
            if resp.status_code == 429:
                time.sleep(backoff * (2**attempt))
                continue
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError) as exc:  # includes JSON decode errors
            last_exc = exc
            time.sleep(backoff * (2**attempt))
    raise RuntimeError(f"GET {url} failed after {retries} attempts: {last_exc}")


def get_text(url: str, params: dict, *, retries: int = 3, backoff: float = 0.6) -> str:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = httpx.get(
                url, params=params, timeout=20.0,
                headers={"User-Agent": USER_AGENT},
            )
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as exc:
            last_exc = exc
            time.sleep(backoff * (2**attempt))
    raise RuntimeError(f"GET {url} failed after {retries} attempts: {last_exc}")
