/**
 * Leaderboard — summary stats bar + grid of GraduateCards sorted by score.
 */

import type { AnalyseResponse } from "../lib/types";
import GraduateCard from "./GraduateCard";
import { Trophy, Link, GitFork } from "lucide-react";

interface Props {
  results: AnalyseResponse;
}

function StatPill({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="flex items-center gap-2 rounded-xl bg-white border border-slate-200 px-4 py-2 shadow-sm">
      {icon}
      <span className="text-sm text-slate-500">{label}</span>
      <span className="text-sm font-bold text-slate-800">{value}</span>
    </div>
  );
}

export default function Leaderboard({ results }: Props) {
  const scored = results.graduates.filter((g) => g.score_result.score > 0);
  const unscored = results.graduates.filter((g) => g.score_result.score === 0);

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="flex flex-wrap gap-3">
        <StatPill
          icon={<Trophy className="h-4 w-4 text-yellow-500" />}
          label="Graduates"
          value={results.total_graduates}
        />
        <StatPill
          icon={<Link className="h-4 w-4 text-blue-600" />}
          label="LinkedIn found"
          value={results.graduates_with_linkedin}
        />
        <StatPill
          icon={<GitFork className="h-4 w-4 text-slate-700" />}
          label="GitHub found"
          value={results.graduates_with_github}
        />
      </div>

      {/* Ranked cards */}
      {scored.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-bold text-slate-800">
            Cracked Classmates <span className="text-slate-400 font-normal text-sm">— ranked by score</span>
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {scored.map((grad, i) => (
              <GraduateCard key={grad.name} graduate={grad} rank={i + 1} />
            ))}
          </div>
        </section>
      )}

      {/* Unscored section */}
      {unscored.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-semibold text-slate-500 uppercase tracking-wide">
            No online presence found ({unscored.length})
          </h2>
          <div className="flex flex-wrap gap-2">
            {unscored.map((g) => (
              <span key={g.name} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500">
                {g.name}
              </span>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
