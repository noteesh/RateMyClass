"""
Stage 3 — GitHub Signals: Find and collect public GitHub stats for each graduate.

The GitHub REST API is free. Without a token you get 60 req/hr; with a free
personal access token (no scopes needed) you get 5,000 req/hr.

For each graduate we:
  1. Search GitHub for a user whose full name matches.
  2. If found, fetch their public repo list and aggregate stats.
"""

import re
import time

import httpx
from rich.console import Console

from backend.config import settings

console = Console()

GITHUB_API = "https://api.github.com"


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    return headers


def _search_by_name(name: str) -> str | None:
    """
    Search GitHub for a user matching the given full name.
    Returns the GitHub username (login) of the top match, or None.
    """
    try:
        resp = httpx.get(
            f"{GITHUB_API}/search/users",
            params={"q": f'"{name}" in:name', "per_page": 1},
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return items[0]["login"] if items else None
    except Exception as e:
        console.print(f"[yellow]GitHub name search failed for {name}: {e}[/yellow]")
        return None


def _get_user_stats(username: str) -> dict:
    """
    Fetch a GitHub user's public profile + repo stats.

    Returns a dict with: username, followers, repos, total_stars, top_languages, bio.
    """
    stats: dict = {
        "username": username,
        "profile_url": f"https://github.com/{username}",
        "followers": 0,
        "repos": 0,
        "total_stars": 0,
        "top_languages": [],
        "bio": None,
    }

    try:
        # User profile
        user_resp = httpx.get(f"{GITHUB_API}/users/{username}", headers=_headers(), timeout=15)
        user_resp.raise_for_status()
        user = user_resp.json()
        stats["followers"] = user.get("followers", 0)
        stats["repos"] = user.get("public_repos", 0)
        stats["bio"] = user.get("bio")

        # Repos (sorted by stars so top repos come first in the 100-item page)
        repos_resp = httpx.get(
            f"{GITHUB_API}/users/{username}/repos",
            params={"per_page": 100, "sort": "stars", "direction": "desc"},
            headers=_headers(),
            timeout=15,
        )
        if repos_resp.status_code == 200:
            repos = repos_resp.json()
            stats["total_stars"] = sum(r.get("stargazers_count", 0) for r in repos)

            # Count repos per language to find the top ones
            lang_counts: dict[str, int] = {}
            for repo in repos:
                lang = repo.get("language")
                if lang:
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1
            stats["top_languages"] = sorted(lang_counts, key=lang_counts.get, reverse=True)[:5]  # type: ignore[arg-type]

    except Exception as e:
        console.print(f"[yellow]GitHub stats failed for {username}: {e}[/yellow]")

    return stats


def _extract_username_from_linkedin(linkedin_data: dict | None) -> str | None:
    """
    Some LinkedIn snippets mention a person's GitHub handle.
    Try to extract it so we can skip the name-search step.
    """
    if not linkedin_data:
        return None
    snippet = linkedin_data.get("google_snippet") or ""
    match = re.search(r"github\.com/([A-Za-z0-9_-]+)", snippet)
    return match.group(1) if match else None


def enrich_with_github(grad: dict) -> dict:
    """
    Attach GitHub stats to a single graduate dict.
    Adds a 'github' key: either a stats dict or None if no account is found.
    """
    name = grad.get("name", "")

    # Prefer a GitHub handle surfaced from the LinkedIn snippet
    username = _extract_username_from_linkedin(grad.get("linkedin"))
    if not username:
        username = _search_by_name(name)

    grad["github"] = _get_user_stats(username) if username else None
    time.sleep(settings.GITHUB_SEARCH_DELAY)
    return grad


def enrich_all_with_github(graduates: list[dict]) -> list[dict]:
    """Run GitHub enrichment for every graduate in the list."""
    console.print(f"[cyan]Fetching GitHub signals for {len(graduates)} graduates...[/cyan]")
    return [enrich_with_github(g) for g in graduates]
