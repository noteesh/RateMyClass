"""
Stage 4 — Scoring: Rate each graduate's "cracked-ness" using Gemini 1.5 Flash.

For each graduate we build a compact profile summary from all collected signals
(LinkedIn title/company, GitHub stats) and ask Gemini to return:
  - A score from 1–10
  - A punchy headline explaining the score
  - A list of notable signals
  - A reason to reach out / connect

Graduates with no discoverable online presence receive score 0 and are shown
at the bottom of the leaderboard.
"""

import json
import re

from google import genai
from rich.console import Console

from backend.config import settings

console = Console()

SCORE_PROMPT = """\
You are evaluating how impressive a recent college graduate is based on their
publicly available online presence.

Score them 1–10 on "cracked-ness" — how distinguished, accomplished, or
ahead-of-the-curve they appear for someone who just graduated.

Scoring signals to consider:
  - LinkedIn: current company prestige, job title seniority, role description
  - GitHub: total stars, follower count, number of repos, languages used
  - Graduation honors (Cum Laude, Summa Cum Laude, etc.)
  - Speed of career trajectory (e.g. already at FAANG or a hot startup)

Graduate profile (JSON):
{profile_json}

Return ONLY a JSON object with exactly these fields — no prose, no markdown:
{{
  "score": <integer 1–10>,
  "headline": "<one punchy sentence on why they stand out — or why they don't>",
  "highlights": ["<signal 1>", "<signal 2>", "<signal 3>"],
  "reach_out_reason": "<one sentence on why you would want to connect with them>"
}}
"""


def _build_profile_summary(grad: dict) -> dict:
    """
    Distil all collected data for a graduate down to the fields that matter
    for scoring. Keeps the prompt short to stay within free-tier token limits.
    """
    linkedin = grad.get("linkedin") or {}
    github = grad.get("github") or {}

    return {
        "name": grad.get("name"),
        "degree": grad.get("degree"),
        "major": grad.get("major"),
        "honors": grad.get("honors"),
        "linkedin": {
            "current_title": linkedin.get("current_title"),
            "current_company": linkedin.get("current_company"),
            "profile_snippet": linkedin.get("google_snippet"),
            "url": linkedin.get("url"),
        } if linkedin else None,
        "github": {
            "username": github.get("username"),
            "total_stars": github.get("total_stars", 0),
            "followers": github.get("followers", 0),
            "repos": github.get("repos", 0),
            "top_languages": github.get("top_languages", []),
            "bio": github.get("bio"),
        } if github else None,
    }


def _score_one(grad: dict, client: genai.Client) -> dict:
    """
    Ask Gemini to score a single graduate.
    Returns the grad dict with a 'score_result' key attached.
    """
    summary = _build_profile_summary(grad)
    has_data = summary.get("linkedin") or summary.get("github")

    if not has_data:
        grad["score_result"] = {
            "score": 0,
            "headline": "No public online presence found.",
            "highlights": [],
            "reach_out_reason": "N/A",
        }
        return grad

    prompt = SCORE_PROMPT.format(profile_json=json.dumps(summary, indent=2))

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL_TEXT,
            contents=prompt,
        )
        raw = response.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        result = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(match.group()) if match else {
            "score": 0, "headline": "Parse error", "highlights": [], "reach_out_reason": ""
        }
    except Exception as e:
        console.print(f"[red]Scoring failed for {grad.get('name')}: {e}[/red]")
        result = {"score": 0, "headline": "Scoring error", "highlights": [], "reach_out_reason": ""}

    grad["score_result"] = result
    return grad


def score_all(graduates: list[dict]) -> list[dict]:
    """
    Score every graduate with Gemini and return the list sorted by score (highest first).

    Args:
        graduates : Enriched graduate list (after OCR, LinkedIn, and GitHub stages).

    Returns:
        Same list with 'score_result' added to each entry, sorted descending by score.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    console.print(f"[cyan]Scoring {len(graduates)} graduates with Gemini...[/cyan]")

    scored = []
    for i, grad in enumerate(graduates, 1):
        name = grad.get("name", "?")
        console.print(f"  [{i}/{len(graduates)}] {name}")
        scored.append(_score_one(grad, client))

    scored.sort(key=lambda g: g.get("score_result", {}).get("score", 0), reverse=True)
    return scored
