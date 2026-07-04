"""PubMed skill: recent clinical literature via NCBI E-utilities.

esearch -> PMIDs, esummary -> metadata, efetch -> abstract snippets. Returns
``SourceRecord``s keyed ``PMID:<pmid>``.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from ..models import SourceRecord
from .http import get_json, get_text, ncbi_api_key

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Lung-nodule-CT-AI specialization. The caller passes a `focus` phrase that is
# AND-ed onto this stable base query.
BASE_QUERY = (
    '("pulmonary nodule"[tiab] OR "lung nodule"[tiab] OR "lung neoplasms"[MeSH]) '
    'AND ("tomography, x-ray computed"[MeSH] OR "chest CT"[tiab] OR "low-dose CT"[tiab]) '
    'AND ("artificial intelligence"[tiab] OR "deep learning"[tiab] '
    'OR "computer-aided"[tiab] OR "CAD"[tiab])'
)


def _key_params() -> dict:
    key = ncbi_api_key()
    return {"api_key": key} if key else {}


def _abstract_snippets(pmids: list[str]) -> dict[str, str]:
    if not pmids:
        return {}
    xml = get_text(
        f"{EUTILS}/efetch.fcgi",
        {"db": "pubmed", "id": ",".join(pmids), "rettype": "abstract",
         "retmode": "xml", **_key_params()},
    )
    out: dict[str, str] = {}
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return out
    for article in root.findall(".//PubmedArticle"):
        pmid_el = article.find(".//PMID")
        if pmid_el is None or not pmid_el.text:
            continue
        texts = [
            (el.text or "").strip()
            for el in article.findall(".//Abstract/AbstractText")
        ]
        abstract = " ".join(t for t in texts if t)
        if abstract:
            out[pmid_el.text] = re.sub(r"\s+", " ", abstract)[:600]
    return out


def search_pubmed(focus: str = "triage OR malignancy risk", retmax: int = 12) -> list[SourceRecord]:
    """Search recent literature on AI lung-nodule detection/triage on chest CT."""

    term = f"({BASE_QUERY}) AND ({focus}) AND 2019:2026[pdat]"
    search = get_json(
        f"{EUTILS}/esearch.fcgi",
        {"db": "pubmed", "term": term, "retmode": "json",
         "retmax": retmax, "sort": "date", **_key_params()},
    )
    pmids = search.get("esearchresult", {}).get("idlist", [])
    if not pmids:
        return []

    summary = get_json(
        f"{EUTILS}/esummary.fcgi",
        {"db": "pubmed", "id": ",".join(pmids), "retmode": "json", **_key_params()},
    ).get("result", {})

    snippets = _abstract_snippets(pmids)

    records: list[SourceRecord] = []
    for pmid in pmids:
        meta = summary.get(pmid, {})
        if not meta:
            continue
        year = (meta.get("pubdate") or "")[:4]
        records.append(
            SourceRecord(
                cite_id=f"PMID:{pmid}",
                kind="pubmed",
                title=meta.get("title", "").rstrip(". "),
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                payload={
                    "journal": meta.get("fulljournalname") or meta.get("source", ""),
                    "year": year,
                    "abstract_snippet": snippets.get(pmid, ""),
                },
            )
        )
    return records
