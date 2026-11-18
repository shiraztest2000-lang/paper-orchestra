"""Free, no-account scholarly discovery across open metadata services.

Searches OpenAlex, Crossref, Europe PMC and arXiv. None of these discovery
endpoints requires an end-user account or API key for ordinary low-volume use.
Results are metadata candidates; full-text availability depends on each work's
open-access status and repository/publisher license.
"""
from __future__ import annotations

import re
import threading
import time
import xml.etree.ElementTree as ET

import requests

TIMEOUT = 20
USER_AGENT = "SHZ-PaperOrchestra/0.3 (no-account academic literature discovery)"
_ARXIV_LOCK = threading.Lock()
_ARXIV_LAST_REQUEST = 0.0


def _cutoff_year(cutoff_date: str | None) -> int | None:
    if not cutoff_date:
        return None
    try:
        return int(cutoff_date.split("-")[0])
    except (TypeError, ValueError):
        return None


def _clean_title(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def _add_candidate(found: dict, title: str, year, source: str,
                   url: str = "", cutoff_year: int | None = None,
                   detail: str = "") -> None:
    title = _clean_title(title)
    try:
        if isinstance(year, str):
            match = re.match(r"\s*(\d{4})", year)
            year = int(match.group(1)) if match else int(year)
        else:
            year = int(year)
    except (TypeError, ValueError):
        return
    if not title or year < 1500 or (cutoff_year and year > cutoff_year):
        return
    key = re.sub(r"[^\w]+", "", title.casefold(), flags=re.UNICODE)
    if not key:
        return
    if key not in found:
        found[key] = {
            "title": title,
            "year": year,
            "reason": f"{source} scholarly index" + (f"; {detail}" if detail else ""),
            "source": source,
            "sources": [source],
            "url": url or "",
        }
    else:
        item = found[key]
        if source not in item["sources"]:
            item["sources"].append(source)
            item["reason"] += f"; also indexed by {source}"
        if not item.get("url") and url:
            item["url"] = url


def _search_openalex(query: str, cutoff_year: int | None, limit: int,
                     headers: dict, found: dict) -> None:
    response = requests.get(
        "https://api.openalex.org/works",
        params={
            "search": query,
            "per-page": min(max(limit, 1), 25),
            "select": "id,doi,display_name,publication_year,cited_by_count,open_access,best_oa_location",
        },
        headers=headers,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    for work in response.json().get("results", []):
        doi = (work.get("doi") or "").replace("https://doi.org/", "")
        oa = work.get("open_access") or {}
        location = work.get("best_oa_location") or {}
        oa_url = location.get("landing_page_url") or location.get("pdf_url") or ""
        url = oa_url or (f"https://doi.org/{doi}" if doi else work.get("id", ""))
        access = "open access" if oa.get("is_oa") else "full text not confirmed open"
        _add_candidate(
            found, work.get("display_name", ""), work.get("publication_year"),
            "OpenAlex", url, cutoff_year,
            f"citations: {work.get('cited_by_count', 0)}; {access}",
        )


def _search_crossref(query: str, cutoff_year: int | None, limit: int,
                     headers: dict, found: dict) -> None:
    response = requests.get(
        "https://api.crossref.org/works",
        params={
            "query.bibliographic": query,
            "rows": min(max(limit, 1), 25),
            "select": "title,DOI,published-print,published-online,published,created",
        },
        headers=headers,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    for work in response.json().get("message", {}).get("items", []):
        titles = work.get("title") or []
        date_obj = (
            work.get("published-print") or work.get("published-online")
            or work.get("published") or work.get("created") or {}
        )
        date_parts = date_obj.get("date-parts", [[]])[0]
        doi = work.get("DOI", "")
        _add_candidate(
            found, titles[0] if titles else "",
            date_parts[0] if date_parts else None,
            "Crossref", f"https://doi.org/{doi}" if doi else "",
            cutoff_year,
        )


def _search_europe_pmc(query: str, cutoff_year: int | None, limit: int,
                        headers: dict, found: dict) -> None:
    response = requests.get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={
            "query": query,
            "format": "json",
            "resultType": "lite",
            "pageSize": min(max(limit, 1), 25),
            "sort": "P_PDATE_D",
        },
        headers=headers,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    for work in response.json().get("resultList", {}).get("result", []):
        doi = work.get("doi", "")
        pmcid = work.get("pmcid", "")
        pmid = work.get("pmid", "")
        url = (
            f"https://europepmc.org/articles/{pmcid}" if pmcid
            else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid
            else f"https://doi.org/{doi}" if doi else ""
        )
        access = "open access" if str(work.get("isOpenAccess", "N")).upper() in {"Y", "TRUE"} else "open access not confirmed"
        _add_candidate(
            found, work.get("title", ""),
            work.get("firstPublicationDate", work.get("pubYear")),
            "Europe PMC", url, cutoff_year, access,
        )


def _search_arxiv(query: str, cutoff_year: int | None, limit: int,
                  headers: dict, found: dict) -> None:
    # arXiv asks clients to avoid rapid repeated API calls. Serialize and space
    # requests so concurrent literature tasks remain polite to the public API.
    global _ARXIV_LAST_REQUEST
    with _ARXIV_LOCK:
        wait = 3.0 - (time.monotonic() - _ARXIV_LAST_REQUEST)
        if wait > 0:
            time.sleep(wait)
        response = requests.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": f'all:"{query}"',
                "start": 0,
                "max_results": min(max(limit, 1), 25),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
            headers=headers,
            timeout=TIMEOUT,
        )
        _ARXIV_LAST_REQUEST = time.monotonic()
    response.raise_for_status()
    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", default="", namespaces=ns)
        published = entry.findtext("atom:published", default="", namespaces=ns)
        link = entry.find("atom:id", ns)
        year = published[:4] if published else None
        _add_candidate(
            found, title, year, "arXiv",
            link.text.strip() if link is not None and link.text else "",
            cutoff_year,
        )


def search_academic_candidates(
    query: str,
    cutoff_date: str | None = None,
    limit: int = 15,
    sources: list[str] | None = None,
) -> list[dict]:
    """Search no-registration scholarly indexes and merge duplicate titles.

    Supported sources: openalex, crossref, europepmc, arxiv. All are enabled
    by default. Pass a subset through the sources argument to narrow the search.
    """
    query = (query or "").strip()
    if not query:
        return []
    cutoff_year = _cutoff_year(cutoff_date)
    headers = {"User-Agent": USER_AGENT}
    found: dict[str, dict] = {}
    selected = set(sources or ["openalex", "crossref", "europepmc", "arxiv"])
    adapters = [
        ("openalex", _search_openalex),
        ("crossref", _search_crossref),
        ("europepmc", _search_europe_pmc),
        ("arxiv", _search_arxiv),
    ]
    for source, adapter in adapters:
        if source not in selected:
            continue
        try:
            adapter(query, cutoff_year, limit, headers, found)
        except (requests.RequestException, ET.ParseError, ValueError, KeyError) as exc:
            print(f"{source} search unavailable: {exc}")
    results = list(found.values())
    results.sort(key=lambda item: (item["year"], item["title"]), reverse=True)
    return results[:max(1, limit)]
