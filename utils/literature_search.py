"""Search scholarly indexes without tying literature discovery to an LLM vendor.

Crossref and OpenAlex provide bibliographic candidate records. These results are
subsequently title-enriched/validated by the existing Semantic Scholar stage.
"""
from __future__ import annotations
import datetime
import re
import requests

TIMEOUT = 20
USER_AGENT = "SHZ-PaperOrchestra/0.2 (academic literature discovery)"

def _cutoff_year(cutoff_date: str | None) -> int | None:
    if not cutoff_date:
        return None
    try:
        return int(cutoff_date.split("-")[0])
    except (TypeError, ValueError):
        return None

def _clean_title(value: str) -> str:
    return re.sub(r"\\s+", " ", (value or "")).strip()

def search_academic_candidates(query: str, cutoff_date: str | None = None, limit: int = 15) -> list[dict]:
    query = (query or "").strip()
    if not query:
        return []
    cutoff_year = _cutoff_year(cutoff_date)
    headers = {"User-Agent": USER_AGENT}
    found: dict[str, dict] = {}

    # OpenAlex search
    try:
        response = requests.get(
            "https://api.openalex.org/works",
            params={"search": query, "per-page": min(max(limit, 1), 25),
                    "select": "id,display_name,publication_year,cited_by_count"},
            headers=headers, timeout=TIMEOUT,
        )
        response.raise_for_status()
        for work in response.json().get("results", []):
            title = _clean_title(work.get("display_name", ""))
            year = work.get("publication_year")
            if not title or not year or (cutoff_year and int(year) > cutoff_year):
                continue
            key = title.casefold()
            found[key] = {"title": title, "year": int(year),
                          "reason": f"OpenAlex scholarly index; citations: {work.get('cited_by_count', 0)}"}
    except requests.RequestException as exc:
        print(f"OpenAlex search unavailable: {exc}")

    # Crossref supplements coverage where OpenAlex has no matching records.
    try:
        response = requests.get(
            "https://api.crossref.org/works",
            params={"query.bibliographic": query, "rows": min(max(limit, 1), 25),
                    "select": "title,author,published-print,published-online,published,created"},
            headers=headers, timeout=TIMEOUT,
        )
        response.raise_for_status()
        for work in response.json().get("message", {}).get("items", []):
            titles = work.get("title") or []
            title = _clean_title(titles[0] if titles else "")
            date_parts = (work.get("published-print") or work.get("published-online")
                          or work.get("published") or work.get("created") or {}).get("date-parts", [[]])[0]
            year = date_parts[0] if date_parts else None
            if not title or not year or (cutoff_year and int(year) > cutoff_year):
                continue
            key = title.casefold()
            if key not in found:
                found[key] = {"title": title, "year": int(year), "reason": "Crossref bibliographic index"}
    except requests.RequestException as exc:
        print(f"Crossref search unavailable: {exc}")

    results = list(found.values())
    results.sort(key=lambda item: (item["year"], item["title"]), reverse=True)
    return results[:limit]
