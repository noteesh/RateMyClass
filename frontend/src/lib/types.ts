/**
 * Shared TypeScript types — mirrors the Pydantic models in backend/api/models.py.
 * Keep these in sync if you change the backend response shape.
 */

export interface LinkedInData {
  url: string | null;
  current_title: string | null;
  current_company: string | null;
  google_snippet: string | null;
}

export interface GitHubData {
  username: string | null;
  profile_url: string | null;
  followers: number;
  repos: number;
  total_stars: number;
  top_languages: string[];
  bio: string | null;
}

export interface ScoreResult {
  score: number;          // 0–10
  headline: string;
  highlights: string[];
  reach_out_reason: string;
}

export interface Graduate {
  name: string;
  degree: string | null;
  major: string | null;
  honors: string | null;
  linkedin: LinkedInData | null;
  github: GitHubData | null;
  score_result: ScoreResult;
}

export interface AnalyseResponse {
  total_graduates: number;
  graduates_with_linkedin: number;
  graduates_with_github: number;
  graduates: Graduate[];
}

// ---------------------------------------------------------------------------
// Class-wide dashboard stats (mirrors backend/pipeline/stats.py output)
// ---------------------------------------------------------------------------

export interface StatEntry {
  name: string;
  count: number;
}

export interface ClassStats {
  total: number;
  with_linkedin: number;
  with_github: number;
  avg_score: number;
  top_score: number;
  companies: StatEntry[];    // top employers, sorted by count
  roles: StatEntry[];        // SWE / PM / Research / etc.
  industries: StatEntry[];   // Big Tech / Finance / Startup / etc.
  top_languages: StatEntry[]; // GitHub languages across the class
}

// ---------------------------------------------------------------------------
// Streaming pipeline events from POST /api/analyse
// ---------------------------------------------------------------------------

export interface PipelineEvent {
  stage: "ocr" | "linkedin" | "github" | "scoring" | "stats" | "done" | "error";
  message: string;
  data?: AnalyseResponse | ClassStats;
}

export type PipelineStage = PipelineEvent["stage"];
