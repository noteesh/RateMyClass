"""
Stage 2 — LinkedIn Discovery: Find public LinkedIn profiles for each graduate.

Strategy (100% free):
  1. Use the Google Custom Search JSON API (free: 100 queries/day) to search
     for each person's LinkedIn profile URL via:  "Name" site:linkedin.com/in
  2. Parse the top result's title + snippet for job title and company — this
     is publicly available in Google's index without hitting LinkedIn directly.

Free tier limit: 100 Google CSE queries/day. For larger programs, the pipeline
saves intermediate results so you can resume the next day without re-querying.
"""

import re
import time
from urllib.parse import quote_plus

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from backend.config import settings

console = Console()

GOOGLE_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


def _search_linkedin_url(name: str, university: str | None = None) -> dict | None:
    """
    Query Google Custom Search for a person's LinkedIn profile.

    Returns a dict with:
      - linkedin_url  : the linkedin.com/in/... URL (string or None)
      - title         : page title from Google's index (usually "Name | Role at Company")
      - snippet       : short description snippet from Google's index
    """
    if not settings.GOOGLE_CSE_API_KEY or not settings.GOOGLE_CSE_ID:
        console.print("[yellow]GOOGLE_CSE_API_KEY or GOOGLE_CSE_ID not set — skipping LinkedIn search.[/yellow]")
        return None

    # Build a tight query: name + university (if known) restricted to linkedin.com/in
    query_parts = [f'"{name}"', "site:linkedin.com/in"]
    if university:
        query_parts.append(university)
    query = " ".join(query_parts)

    try:
        resp = httpx.get(
            GOOGLE_CSE_ENDPOINT,
            params={
                "key": settings.GOOGLE_CSE_API_KEY,
                "cx": settings.GOOGLE_CSE_ID,
                "q": query,
                "num": 1,           # we only need the top result
            },
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return None

        top = items[0]
        return {
            "linkedin_url": top.get("link"),
            "title": top.get("title", ""),
            "snippet": top.get("snippet", ""),
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            console.print("[red]Google CSE daily quota exhausted (100/day). Resume tomorrow.[/red]")
        else:
            console.print(f"[red]Google CSE error for {name}: {e.response.status_code}[/red]")
        return None
    except Exception as e:
        console.print(f"[yellow]LinkedIn search failed for {name}: {e}[/yellow]")
        return None


def _parse_role_from_google_result(title: str, snippet: str) -> dict:
    """
    Extract job title and company from a Google search result title/snippet.

    LinkedIn page titles usually follow the pattern:
      "First Last - Job Title at Company | LinkedIn"
    or
      "First Last - Company | LinkedIn"
    """
    result = {"current_title": None, "current_company": None}

    # Strip " | LinkedIn" suffix
    cleaned = re.sub(r"\s*\|\s*LinkedIn.*$", "", title).strip()

    # Try "Name - Title at Company"
    at_match = re.search(r"-\s*(.+?)\s+at\s+(.+)$", cleaned, re.IGNORECASE)
    if at_match:
        result["current_title"] = at_match.group(1).strip()
        result["current_company"] = at_match.group(2).strip()
        return result

    # Try "Name - Company" (no title visible)
    dash_match = re.search(r"-\s*(.+)$", cleaned)
    if dash_match:
        result["current_company"] = dash_match.group(1).strip()

    return result


def lookup_graduates(
    graduates: list[dict],
    university: str | None = None,
) -> list[dict]:
    """
    For each graduate, search Google for their LinkedIn profile URL + role info.
    Attaches a 'linkedin' key to each graduate dict.

    Args:
        graduates  : List of graduate dicts from the OCR stage.
        university : University name to narrow Google searches.

    Returns:
        Same list with 'linkedin' key added to each entry.
    """
    enriched = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Searching LinkedIn profiles...", total=len(graduates))

        for grad in graduates:
            name = grad.get("name", "")
            progress.update(task, description=f"Searching: {name}")

            result = _search_linkedin_url(name, university=university)

            linkedin_data = None
            if result:
                role_info = _parse_role_from_google_result(
                    result.get("title", ""), result.get("snippet", "")
                )
                linkedin_data = {
                    "url": result.get("linkedin_url"),
                    "current_title": role_info["current_title"],
                    "current_company": role_info["current_company"],
                    "google_snippet": result.get("snippet"),
                }

            enriched.append({**grad, "linkedin": linkedin_data})

            # Respect Google's rate limit — stay well under 100/day quota
            time.sleep(settings.LINKEDIN_SEARCH_DELAY)
            progress.advance(task)

    found = sum(1 for g in enriched if g["linkedin"])
    console.print(f"[green]Found LinkedIn data for {found}/{len(graduates)} graduates.[/green]")
    return enriched
