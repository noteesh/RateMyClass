/**
 * Dashboard — class-wide statistics view.
 *
 * Shows four sections:
 *  1. Summary stat pills  (total, LinkedIn found, avg score, top score)
 *  2. Top Employers       (horizontal bar chart — most impactful for networking)
 *  3. Role Breakdown      (donut chart — SWE vs PM vs Research vs other)
 *  4. Industry Breakdown  (donut chart — Big Tech vs Finance vs Startup etc.)
 *
 * Receives ClassStats as a prop; re-renders automatically when the parent
 * passes updated stats (e.g. after the "stats" streaming event arrives).
 */

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Legend,
} from "recharts";
import type { ClassStats } from "../lib/types";
import { Users, Link, Star, TrendingUp } from "lucide-react";

interface Props {
  stats: ClassStats;
  isLive?: boolean;  // true while the pipeline is still running
}

// Colour palette for charts — indigo-based to match the app theme
const BAR_COLORS = [
  "#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe",
  "#e0e7ff", "#6366f1", "#818cf8", "#a5b4fc",
];

const PIE_COLORS = [
  "#6366f1", "#f59e0b", "#10b981", "#ef4444",
  "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6",
];


// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatPill({
  icon, label, value, sub,
}: {
  icon: React.ReactNode; label: string; value: string | number; sub?: string;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
      <div className="flex items-center gap-2 text-slate-500 text-xs font-medium uppercase tracking-wide">
        {icon}
        {label}
      </div>
      <p className="text-3xl font-black text-slate-900">{value}</p>
      {sub && <p className="text-xs text-slate-400">{sub}</p>}
    </div>
  );
}

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h2 className="text-lg font-bold text-slate-800">{title}</h2>
      {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center h-32 rounded-xl bg-slate-50 border border-dashed border-slate-200">
      <p className="text-sm text-slate-400">{message}</p>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Custom tooltip shared by both chart types
// ---------------------------------------------------------------------------

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { name: string; value: number }[] }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-lg text-sm">
      <p className="font-semibold text-slate-800">{payload[0].name}</p>
      <p className="text-indigo-600 font-bold">{payload[0].value} people</p>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Main Dashboard component
// ---------------------------------------------------------------------------

export default function Dashboard({ stats, isLive = false }: Props) {
  const topCompanies = stats.companies.slice(0, 12);
  const roles = stats.roles.filter((r) => r.count > 0);
  const industries = stats.industries.filter((r) => r.count > 0);

  return (
    <div className="space-y-8">
      {/* Live indicator */}
      {isLive && (
        <div className="flex items-center gap-2 text-sm text-amber-600 font-medium">
          <span className="inline-block h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
          Updating live as the pipeline runs…
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Summary pills                                                        */}
      {/* ------------------------------------------------------------------ */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatPill
          icon={<Users className="h-3.5 w-3.5" />}
          label="Graduates"
          value={stats.total}
        />
        <StatPill
          icon={<Link className="h-3.5 w-3.5" />}
          label="LinkedIn Found"
          value={stats.with_linkedin}
          sub={`${Math.round((stats.with_linkedin / Math.max(stats.total, 1)) * 100)}% of class`}
        />
        <StatPill
          icon={<TrendingUp className="h-3.5 w-3.5" />}
          label="Avg Score"
          value={stats.avg_score > 0 ? `${stats.avg_score}/10` : "—"}
          sub="among scored graduates"
        />
        <StatPill
          icon={<Star className="h-3.5 w-3.5" />}
          label="Top Score"
          value={stats.top_score > 0 ? `${stats.top_score}/10` : "—"}
        />
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Top Employers — horizontal bar chart                                */}
      {/* ------------------------------------------------------------------ */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <SectionHeader
          title="Top Employers"
          subtitle="Companies where the most graduates landed"
        />
        {topCompanies.length === 0 ? (
          <EmptyState message="No company data yet — waiting for LinkedIn results" />
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(200, topCompanies.length * 36)}>
            <BarChart
              data={topCompanies}
              layout="vertical"
              margin={{ top: 0, right: 24, left: 8, bottom: 0 }}
            >
              <XAxis type="number" tick={{ fontSize: 12 }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="name"
                width={140}
                tick={{ fontSize: 12 }}
                tickLine={false}
              />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="count" radius={[0, 6, 6, 0]} maxBarSize={28}>
                {topCompanies.map((_, i) => (
                  <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Role + Industry donuts — side by side                               */}
      {/* ------------------------------------------------------------------ */}
      <div className="grid gap-6 md:grid-cols-2">

        {/* Role breakdown */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <SectionHeader
            title="Role Breakdown"
            subtitle="What your classmates are actually doing"
          />
          {roles.length === 0 ? (
            <EmptyState message="No role data yet" />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={roles}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                >
                  {roles.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
                <Legend
                  iconType="circle"
                  iconSize={8}
                  formatter={(value) => <span className="text-xs text-slate-600">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Industry breakdown */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <SectionHeader
            title="Industry Breakdown"
            subtitle="Where the class ended up by sector"
          />
          {industries.length === 0 ? (
            <EmptyState message="No industry data yet" />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={industries}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                >
                  {industries.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
                <Legend
                  iconType="circle"
                  iconSize={8}
                  formatter={(value) => <span className="text-xs text-slate-600">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* GitHub languages — only shown if GitHub data was collected           */}
      {/* ------------------------------------------------------------------ */}
      {stats.top_languages.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <SectionHeader
            title="Class Programming Languages"
            subtitle="Most-used languages across all GitHub profiles found"
          />
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.top_languages} margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fontSize: 12 }} tickLine={false} />
              <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={40}>
                {stats.top_languages.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
