"""
FastAPI route definitions.

POST /api/analyse
  Accepts a multipart form upload (program photo + optional metadata).
  Runs the full pipeline and streams back results as newline-delimited JSON
  so the frontend can update the UI stage by stage.

GET /api/health
  Simple liveness check.
"""

import json
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from backend.pipeline import ocr, linkedin, github, scorer, stats
from backend.api.models import AnalyseResponse, Graduate, LinkedInData, GitHubData, ScoreResult

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@router.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Main analysis endpoint
# ---------------------------------------------------------------------------

@router.post("/analyse")
async def analyse(
    file: UploadFile = File(..., description="Commencement program photo (jpg/png/webp)"),
    university: str = Form(None, description="University name — improves LinkedIn search accuracy"),
    graduation_year: int = Form(None, description="Graduation year"),
    skip_github: bool = Form(False, description="Skip GitHub enrichment to save time"),
):
    """
    Upload a commencement program photo and run the full pipeline:
      1. OCR  → extract graduate names with Gemini Vision
      2. LinkedIn → find profiles via Google Custom Search
      3. GitHub → collect public stats (optional)
      4. Scorer → rate each graduate with Gemini

    Returns a streaming response where each line is a JSON progress event:
      {"stage": "ocr",      "message": "Extracted 87 graduates"}
      {"stage": "linkedin", "message": "Found 62/87 LinkedIn profiles"}
      {"stage": "github",   "message": "GitHub enrichment complete"}
      {"stage": "scoring",  "message": "Scoring complete"}
      {"stage": "stats",    "message": "Stats ready", "data": { ...ClassStats... }}
      {"stage": "done",     "message": "Pipeline complete", "data": { ...AnalyseResponse... }}

    The frontend listens to this stream and updates the UI as each stage completes.
    Stats are emitted before "done" so the Dashboard can render live.
    """
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    async def run_pipeline():
        # Save upload to a temp file so pipeline functions can read it by path
        with tempfile.NamedTemporaryFile(suffix=Path(file.filename or "upload.jpg").suffix, delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = Path(tmp.name)

        try:
            # Stage 1 — OCR
            yield _event("ocr", "Running Gemini Vision OCR on photo...")
            graduates = ocr.extract_graduates(tmp_path, university=university)
            yield _event("ocr", f"Extracted {len(graduates)} graduates from photo")

            # Stage 2 — LinkedIn
            yield _event("linkedin", "Searching LinkedIn profiles via Google...")
            graduates = linkedin.lookup_graduates(graduates, university=university)
            found_li = sum(1 for g in graduates if g.get("linkedin"))
            yield _event("linkedin", f"Found {found_li}/{len(graduates)} LinkedIn profiles")

            # Stage 3 — GitHub (optional)
            if not skip_github:
                yield _event("github", "Fetching GitHub signals...")
                graduates = github.enrich_all_with_github(graduates)
                found_gh = sum(1 for g in graduates if g.get("github"))
                yield _event("github", f"Found {found_gh}/{len(graduates)} GitHub profiles")

            # Stage 4 — Scoring
            yield _event("scoring", "Scoring graduates with Gemini...")
            graduates = scorer.score_all(graduates)
            yield _event("scoring", "Scoring complete")

            # Stage 5 — Class-wide stats (sent before "done" so Dashboard renders live)
            class_stats = stats.compute_stats(graduates)
            yield _event("stats", "Class stats ready", data=class_stats)

            # Final payload — full graduate list for the Leaderboard
            response = _build_response(graduates)
            yield _event("done", "Pipeline complete", data=response.model_dump())

        finally:
            tmp_path.unlink(missing_ok=True)

    return StreamingResponse(run_pipeline(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _event(stage: str, message: str, data: dict | None = None) -> str:
    """Serialize a pipeline progress event as a newline-terminated JSON string."""
    payload: dict = {"stage": stage, "message": message}
    if data is not None:
        payload["data"] = data
    return json.dumps(payload) + "\n"


def _build_response(graduates: list[dict]) -> AnalyseResponse:
    """Convert raw pipeline output dicts into typed Pydantic models."""
    typed: list[Graduate] = []
    for g in graduates:
        li = g.get("linkedin") or {}
        gh = g.get("github") or {}
        sr = g.get("score_result") or {}

        typed.append(Graduate(
            name=g.get("name", ""),
            degree=g.get("degree"),
            major=g.get("major"),
            honors=g.get("honors"),
            linkedin=LinkedInData(**li) if li else None,
            github=GitHubData(**gh) if gh else None,
            score_result=ScoreResult(
                score=sr.get("score", 0),
                headline=sr.get("headline", ""),
                highlights=sr.get("highlights", []),
                reach_out_reason=sr.get("reach_out_reason", ""),
            ),
        ))

    return AnalyseResponse(
        total_graduates=len(typed),
        graduates_with_linkedin=sum(1 for g in typed if g.linkedin),
        graduates_with_github=sum(1 for g in typed if g.github),
        graduates=typed,
    )
