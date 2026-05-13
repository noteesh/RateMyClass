"""
Pydantic models for API request and response shapes.

Keeping these separate from pipeline logic means the frontend always gets
a predictable, documented schema — and changing internals won't break the API
as long as these models stay stable.
"""

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

class LinkedInData(BaseModel):
    url: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    google_snippet: str | None = None


class GitHubData(BaseModel):
    username: str | None = None
    profile_url: str | None = None
    followers: int = 0
    repos: int = 0
    total_stars: int = 0
    top_languages: list[str] = []
    bio: str | None = None


class ScoreResult(BaseModel):
    score: int = 0                          # 0–10; 0 means no data found
    headline: str = ""
    highlights: list[str] = []
    reach_out_reason: str = ""


# ---------------------------------------------------------------------------
# Per-graduate response model
# ---------------------------------------------------------------------------

class Graduate(BaseModel):
    name: str
    degree: str | None = None
    major: str | None = None
    honors: str | None = None
    linkedin: LinkedInData | None = None
    github: GitHubData | None = None
    score_result: ScoreResult = ScoreResult()


# ---------------------------------------------------------------------------
# API request model (multipart form handled in the route; this is for docs)
# ---------------------------------------------------------------------------

class AnalyseRequest(BaseModel):
    university: str | None = None
    graduation_year: int | None = None
    skip_github: bool = False


# ---------------------------------------------------------------------------
# API response model
# ---------------------------------------------------------------------------

class AnalyseResponse(BaseModel):
    total_graduates: int
    graduates_with_linkedin: int
    graduates_with_github: int
    graduates: list[Graduate]
