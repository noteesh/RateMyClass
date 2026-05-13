"""
Central configuration — reads from environment variables / .env file.

All API keys and tunable constants live here so nothing is hardcoded
in pipeline or API code.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # -------------------------------------------------------------------------
    # Gemini (Google AI Studio) — free tier, used for OCR + scoring
    # Get your key at: https://aistudio.google.com/app/apikey
    # -------------------------------------------------------------------------
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_VISION: str = "gemini-1.5-flash"   # handles image input
    GEMINI_MODEL_TEXT: str = "gemini-1.5-flash"     # used for scoring

    # -------------------------------------------------------------------------
    # Google Custom Search — free tier: 100 queries/day
    # Create a search engine at: https://programmablesearchengine.google.com
    # Get an API key at: https://console.cloud.google.com (Custom Search JSON API)
    # -------------------------------------------------------------------------
    GOOGLE_CSE_API_KEY: str = os.getenv("GOOGLE_CSE_API_KEY", "")
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID", "")     # "cx" value from your search engine

    # -------------------------------------------------------------------------
    # GitHub — optional, but raises rate limit from 60 to 5000 req/hr
    # Create a token at: https://github.com/settings/tokens (no scopes needed)
    # -------------------------------------------------------------------------
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # -------------------------------------------------------------------------
    # Pipeline behaviour
    # -------------------------------------------------------------------------
    LINKEDIN_SEARCH_DELAY: float = 1.0    # seconds between Google CSE calls (stay under quota)
    GITHUB_SEARCH_DELAY: float = 0.3      # seconds between GitHub API calls
    MAX_GRADUATES_PER_RUN: int = 100      # safety cap; increase if needed

    # -------------------------------------------------------------------------
    # FastAPI server
    # -------------------------------------------------------------------------
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
