/**
 * GraduateCard — detailed card shown for each graduate in the leaderboard.
 * Displays score, headline, highlights, and links to LinkedIn / GitHub.
 */

import { GitFork, Link, Star, Users, ExternalLink } from "lucide-react";
import type { Graduate } from "../lib/types";

interface Props {
  graduate: Graduate;
  rank: number;
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 8 ? "bg-green-100 text-green-700 ring-green-200" :
    score >= 5 ? "bg-yellow-100 text-yellow-700 ring-yellow-200" :
                 "bg-slate-100 text-slate-500 ring-slate-200";
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-bold ring-1 ${color}`}>
      {score}/10
    </span>
  );
}

export default function GraduateCard({ graduate, rank }: Props) {
  const { name, degree, major, honors, linkedin, github, score_result } = graduate;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white text-sm font-bold">
            {rank}
          </span>
          <div>
            <h3 className="font-semibold text-slate-900">{name}</h3>
            <p className="text-xs text-slate-500">
              {[major, degree, honors].filter(Boolean).join(" · ")}
            </p>
          </div>
        </div>
        <ScoreBadge score={score_result.score} />
      </div>

      {/* Headline */}
      {score_result.headline && (
        <p className="mt-3 text-sm text-slate-600 italic">{score_result.headline}</p>
      )}

      {/* Current role */}
      {(linkedin?.current_title || linkedin?.current_company) && (
        <p className="mt-2 text-sm font-medium text-slate-700">
          {[linkedin.current_title, linkedin.current_company].filter(Boolean).join(" @ ")}
        </p>
      )}

      {/* Highlights */}
      {score_result.highlights.length > 0 && (
        <ul className="mt-3 space-y-1">
          {score_result.highlights.map((h, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
              <span className="mt-0.5 text-indigo-500">•</span>
              {h}
            </li>
          ))}
        </ul>
      )}

      {/* GitHub stats */}
      {github && (
        <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <Star className="h-3.5 w-3.5 text-yellow-400" />
            {github.total_stars} stars
          </span>
          <span className="flex items-center gap-1">
            <Users className="h-3.5 w-3.5" />
            {github.followers} followers
          </span>
          {github.top_languages.length > 0 && (
            <span className="text-slate-400">
              {github.top_languages.slice(0, 3).join(" · ")}
            </span>
          )}
        </div>
      )}

      {/* Links */}
      <div className="mt-4 flex items-center gap-3">
        {linkedin?.url && (
          <a
            href={linkedin.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700"
          >
            <Link className="h-3.5 w-3.5" />
            LinkedIn
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
        {github?.profile_url && (
          <a
            href={github.profile_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs font-medium text-slate-700 hover:text-slate-900"
          >
            <GitFork className="h-3.5 w-3.5" />
            GitHub
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>

      {/* Reach-out reason */}
      {score_result.reach_out_reason && score_result.reach_out_reason !== "N/A" && (
        <div className="mt-3 rounded-lg bg-indigo-50 px-3 py-2 text-xs text-indigo-700">
          <span className="font-semibold">Why connect: </span>
          {score_result.reach_out_reason}
        </div>
      )}
    </div>
  );
}
