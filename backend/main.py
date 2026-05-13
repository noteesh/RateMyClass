"""
Backend entry point — starts the FastAPI server.

Run with:
    uvicorn backend.main:app --reload --port 8000

Or via the helper script:
    python -m backend.main
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import settings

app = FastAPI(
    title="RateMyClass API",
    description="Find and rank the most impressive graduates from a commencement program photo.",
    version="1.0.0",
)

# Allow the Vite dev server (port 5173) and any production origin to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
