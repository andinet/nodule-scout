"""MAUDE skill: FDA device adverse-event reports via openFDA.

Mines the FDA's MAUDE database for reported software/device failures in devices
adjacent to AI lung-nodule detection/triage. openFDA free-text is noisy, so we
scope to radiology CADe/CADx device names and report counts honestly. Returns
``SourceRecord``s keyed ``MAUDE:<mdr_report_key>``.
"""

from __future__ import annotations

from ..models import SourceRecord
from .http import get_json, openfda_api_key

ENDPOINT = "https://api.fda.gov/device/event.json"

# MAUDE holds almost no adverse events under the newest AI lung-triage brand
# names, so we search the broader computer-assisted-detection device space these
# products are predicated on. Note: "CAD" collides with dental CAD/CAM, so the
# result set is deliberately noisy — the orchestrator is told to filter and to
# report the sparseness honestly (itself a Phase 01 signal).
DEFAULT_SEARCH = (
    'device.generic_name:"computer aided detection" '
    'OR device.openfda.device_name:"computer assisted"'
)


def _key_params() -> dict:
    key = openfda_api_key()
    return {"api_key": key} if key else {}


def _first(value) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def search_maude(search: str = DEFAULT_SEARCH, limit: int = 15) -> list[SourceRecord]:
    """Query MAUDE for adverse events on lung-imaging / CAD devices."""

    data = get_json(
        ENDPOINT,
        {"search": search, "limit": limit, "sort": "date_received:desc", **_key_params()},
    )
    results = data.get("results", [])
    total = data.get("meta", {}).get("results", {}).get("total", 0)

    records: list[SourceRecord] = []
    for i, event in enumerate(results):
        key = event.get("mdr_report_key") or event.get("report_number") or f"idx{i}"
        device = (event.get("device") or [{}])[0]
        openfda = device.get("openfda", {})
        problems = event.get("product_problems") or []
        narrative = ""
        for mdr in event.get("mdr_text") or []:
            if mdr.get("text"):
                narrative = mdr["text"][:400]
                break
        records.append(
            SourceRecord(
                cite_id=f"MAUDE:{key}",
                kind="maude",
                title=(
                    _first(openfda.get("device_name"))
                    or device.get("generic_name")
                    or device.get("brand_name")
                    or "MAUDE adverse event report"
                ),
                url=f"https://api.fda.gov/device/event.json?search=mdr_report_key:{key}",
                payload={
                    "event_type": _first(event.get("event_type")),
                    "date_received": event.get("date_received", ""),
                    "manufacturer": device.get("manufacturer_d_name", ""),
                    "brand_name": device.get("brand_name", ""),
                    "product_problems": problems,
                    "narrative_snippet": narrative,
                    "match_total": total,
                },
            )
        )
    return records
