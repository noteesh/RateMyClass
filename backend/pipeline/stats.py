"""
Stats aggregator — computes class-wide dashboard metrics from scored graduates.

Called after the scoring stage. Takes the full graduate list and returns a
ClassStats dict that the frontend renders as charts.

All classification is done with simple keyword matching so it works without
any extra API calls. Gemini already extracted role/company from LinkedIn snippets.
"""

import re
from collections import Counter


# ---------------------------------------------------------------------------
# Industry classification — keyword → industry label
# Order matters: first match wins
# ---------------------------------------------------------------------------
INDUSTRY_RULES: list[tuple[str, list[str]]] = [
    ("Big Tech",     ["google", "meta", "apple", "amazon", "microsoft", "netflix", "nvidia", "openai", "anthropic", "deepmind"]),
    ("Finance",      ["bank", "goldman", "jpmorgan", "morgan stanley", "citadel", "two sigma", "jane street", "capital", "trading", "fintech", "stripe", "robinhood", "coinbase", "hedge"]),
    ("Healthcare",   ["health", "medical", "pharma", "hospital", "clinic", "biotech", "bio", "genomics"]),
    ("Consulting",   ["mckinsey", "bain", "bcg", "deloitte", "accenture", "pwc", "kpmg", "consulting"]),
    ("Government",   ["government", "federal", "nasa", "dod", "darpa", "army", "navy", "air force", "national lab", "intelligence"]),
    ("Startup",      ["startup", "ventures", "inc.", " llc", "labs", "technologies", "solutions"]),
    ("Academia",     ["university", "college", "research institute", "phd", "professor", "postdoc"]),
    ("Tech",         ["software", "saas", "cloud", "data", "ai", "ml", "platform", "systems", "engineering"]),
]

# ---------------------------------------------------------------------------
# Role classification — keyword → role bucket
# ---------------------------------------------------------------------------
ROLE_RULES: list[tuple[str, list[str]]] = [
    ("Software Engineer",    ["software engineer", "swe", "developer", "engineer", "backend", "frontend", "full stack", "fullstack"]),
    ("ML / AI Engineer",     ["machine learning", "ml engineer", "ai engineer", "research engineer", "deep learning", "nlp"]),
    ("Research Scientist",   ["research scientist", "researcher", "scientist", "phd"]),
    ("Product Manager",      ["product manager", "pm ", "product lead", "head of product"]),
    ("Data Scientist",       ["data scientist", "data analyst", "analytics", "quantitative"]),
    ("Founding / Leadership",["founder", "co-founder", "ceo", "cto", "coo", "head of", "director", "vp ", "vice president", "principal"]),
    ("Consultant",           ["consultant", "associate", "analyst"]),
]


def _classify(text: str, rules: list[tuple[str, list[str]]], default: str = "Other") -> str:
    """Run keyword rules against lowercased text; return first match label."""
    lower = text.lower()
    for label, keywords in rules:
        if any(kw in lower for kw in keywords):
            return label
    return default


def _normalize_company(raw: str) -> str:
    """Clean up company names so variants collapse into one bucket."""
    name = raw.strip()
    # Strip legal suffixes
    name = re.sub(r"\s+(Inc\.?|LLC\.?|Ltd\.?|Corp\.?|Co\.?|GmbH)$", "", name, flags=re.IGNORECASE)
    # Title-case for consistency
    return name.title()


def compute_stats(graduates: list[dict]) -> dict:
    """
    Aggregate class-wide statistics from a list of scored graduate dicts.

    Returns a dict with the shape consumed by the frontend Dashboard component:
    {
        "total": int,
        "with_linkedin": int,
        "with_github": int,
        "avg_score": float,
        "top_score": int,
        "companies": [{"name": str, "count": int}, ...],   # top 15
        "roles":     [{"name": str, "count": int}, ...],
        "industries":[{"name": str, "count": int}, ...],
        "top_languages": [{"name": str, "count": int}, ...],  # GitHub
    }
    """
    total = len(graduates)
    with_linkedin = sum(1 for g in graduates if g.get("linkedin"))
    with_github = sum(1 for g in graduates if g.get("github"))

    scores = [g.get("score_result", {}).get("score", 0) for g in graduates]
    scored_scores = [s for s in scores if s > 0]
    avg_score = round(sum(scored_scores) / len(scored_scores), 1) if scored_scores else 0.0
    top_score = max(scores) if scores else 0

    company_counter: Counter = Counter()
    role_counter: Counter = Counter()
    industry_counter: Counter = Counter()
    lang_counter: Counter = Counter()

    for grad in graduates:
        li = grad.get("linkedin") or {}
        gh = grad.get("github") or {}

        company_raw = li.get("current_company") or ""
        title_raw = li.get("current_title") or ""

        # Company
        if company_raw:
            company_counter[_normalize_company(company_raw)] += 1

        # Role
        combined = f"{title_raw} {company_raw}"
        role_counter[_classify(combined, ROLE_RULES, default="Other")] += 1

        # Industry (use company first, fall back to title)
        industry_text = f"{company_raw} {title_raw}"
        industry_counter[_classify(industry_text, INDUSTRY_RULES, default="Other")] += 1

        # GitHub languages
        for lang in gh.get("top_languages", []):
            lang_counter[lang] += 1

    def to_list(counter: Counter, top_n: int = 15) -> list[dict]:
        return [{"name": k, "count": v} for k, v in counter.most_common(top_n)]

    return {
        "total": total,
        "with_linkedin": with_linkedin,
        "with_github": with_github,
        "avg_score": avg_score,
        "top_score": top_score,
        "companies": to_list(company_counter),
        "roles": to_list(role_counter),
        "industries": to_list(industry_counter),
        "top_languages": to_list(lang_counter, top_n=10),
    }
