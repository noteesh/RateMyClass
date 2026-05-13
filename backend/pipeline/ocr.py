"""
Stage 1 — OCR: Extract graduate names from a commencement program photo.

Uses Gemini 1.5 Flash vision (free tier: 1500 req/day via Google AI Studio).
Sends the image and asks Gemini to return a structured JSON list of graduates.
"""

import json
import re
from pathlib import Path

from google import genai
from google.genai import types as genai_types
from PIL import Image
import httpx
from rich.console import Console

from backend.config import settings

console = Console()


EXTRACTION_PROMPT = """\
You are analyzing a photo of a graduation commencement program page.

Your job is to extract every graduate name listed on the page.

For each graduate, return a JSON object with these fields:
  - "name"   : full name exactly as printed (string)
  - "degree" : degree type if shown, e.g. "Master of Computer Science" (string or null)
  - "major"  : field of study / department if shown (string or null)
  - "honors" : any honors next to their name, e.g. "Cum Laude" (string or null)

Rules:
  - Return ONLY a raw JSON array — no markdown fences, no prose.
  - If the page title indicates a degree (e.g. "MASTER OF COMPUTER SCIENCE"), apply
    that degree to every graduate on the page.
  - If no graduates are visible, return an empty array: []
"""


def _load_image(image_path: Path) -> Image.Image:
    """
    Open, resize, and convert image to JPEG so it's small enough to upload
    to Gemini quickly. Phone photos are often 3-8MB; we target under 800KB.
    """
    img = Image.open(image_path).convert("RGB")

    # Cap long edge at 1600px — plenty of resolution for OCR text
    max_dim = 1600
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # Save as compressed JPEG into a BytesIO buffer, then re-open
    # so Gemini receives a small file rather than the raw PIL object
    import io
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75, optimize=True)
    buf.seek(0)
    size_kb = buf.getbuffer().nbytes // 1024
    console.print(f"[dim]Image compressed to {size_kb}KB before upload[/dim]")
    return Image.open(buf)


def extract_graduates(image_path: str | Path, university: str | None = None) -> list[dict]:
    """
    Send a commencement program photo to Gemini Vision and extract graduate records.

    Args:
        image_path : Path to the photo (jpg, png, webp).
        university : Optional university name added to the prompt for context.

    Returns:
        List of dicts — each has: name, degree, major, honors.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=genai_types.HttpOptions(timeout=120),
    )
    img = _load_image(image_path)

    prompt = EXTRACTION_PROMPT
    if university:
        prompt = f"University: {university}\n\n" + prompt

    console.print(f"[cyan]Sending image to Gemini Vision:[/cyan] {image_path.name}")

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL_VISION,
        contents=[prompt, img],
    )
    raw = response.text.strip()

    # Strip markdown code fences if Gemini wraps the output
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        graduates = json.loads(raw)
    except json.JSONDecodeError:
        # Last-resort: pull anything that looks like a JSON array out of the text
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            graduates = json.loads(match.group())
        else:
            console.print("[red]Could not parse Gemini response as JSON.[/red]")
            console.print(raw[:500])
            graduates = []

    console.print(f"[green]Extracted {len(graduates)} graduates from photo.[/green]")
    return graduates
