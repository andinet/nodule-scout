"""510(k) skill: predicate device clearances via openFDA.

Pulls predicate device labeling for AI lung-nodule detection/triage products
from the FDA 510(k) database. Returns ``SourceRecord``s keyed ``510K:<k_number>``
(actually stored as the k_number itself, e.g. ``K233456``).
"""

from __future__ import annotations

from ..models import SourceRecord
from .http import get_json, openfda_api_key

ENDPOINT = "https://api.fda.gov/device/510k.json"

# Radiological CADe/CADx and lung-imaging clearances. POK = radiological
# computer-aided detection; QIH/QFM/MYN cover CAD software families that AI
# lung-nodule products clear against.
DEFAULT_SEARCH = (
    '(device_name:("nodule" "lung" "chest") OR applicant:("Optellum" "Riverain" "Qure" "Lunit")) '
    'AND advisory_committee_description:"Radiology"'
)


def _key_params() -> dict:
    key = openfda_api_key()
    return {"api_key": key} if key else {}


def search_510k(search: str = DEFAULT_SEARCH, limit: int = 15) -> list[SourceRecord]:
    """Query FDA 510(k) clearances for lung-nodule / radiology CAD predicates."""

    data = get_json(
        ENDPOINT,
        {"search": search, "limit": limit, "sort": "decision_date:desc", **_key_params()},
    )
    results = data.get("results", [])
    total = data.get("meta", {}).get("results", {}).get("total", 0)

    records: list[SourceRecord] = []
    for entry in results:
        k = entry.get("k_number", "")
        if not k:
            continue
        records.append(
            SourceRecord(
                cite_id=k,  # e.g. "K233456"
                kind="fda510k",
                title=entry.get("device_name", "").strip(),
                url=(
                    "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/"
                    f"pmn.cfm?ID={k}"
                ),
                payload={
                    "applicant": entry.get("applicant", ""),
                    "decision_date": entry.get("decision_date", ""),
                    "product_code": entry.get("product_code", ""),
                    "clearance_type": entry.get("clearance_type", ""),
                    "match_total": total,
                },
            )
        )
    return records
