/**
 * Home page — the single page of the app.
 *
 * Layout:
 *   1. Header
 *   2. Upload form (always visible so the user can run a new analysis)
 *   3. Pipeline progress bar (shown while the pipeline is running)
 *   4. Tab bar — Leaderboard | Dashboard  (shown once any results arrive)
 *   5. Active tab content
 */

import { useState } from "react";
import UploadForm from "../components/UploadForm";
import PipelineProgress from "../components/PipelineProgress";
import Leaderboard from "../components/Leaderboard";
import Tabs from "../components/Tabs";
import Dashboard from "./Dashboard";
import { usePipeline } from "../hooks/usePipeline";
import { GraduationCap } from "lucide-react";

type TabId = "leaderboard" | "dashboard";

export default function Home() {
  const { isLoading, completedStages, currentStage, messages, results, stats, error, run } =
    usePipeline();

  const [activeTab, setActiveTab] = useState<TabId>("leaderboard");

  // Show results area as soon as either leaderboard or stats have arrived
  const hasAnyResults = results !== null || stats !== null;

  const tabs = [
    { id: "leaderboard", label: "Leaderboard", badge: results?.total_graduates },
    { id: "dashboard",   label: "Dashboard" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50">
      <div className="mx-auto max-w-6xl px-4 py-12 space-y-8">

        {/* ---------------------------------------------------------------- */}
        {/* Header                                                            */}
        {/* ---------------------------------------------------------------- */}
        <header className="text-center space-y-2">
          <div className="flex items-center justify-center gap-3">
            <GraduationCap className="h-10 w-10 text-indigo-600" />
            <h1 className="text-4xl font-black text-slate-900 tracking-tight">RateMyClass</h1>
          </div>
          <p className="text-slate-500 text-lg">
            Upload a commencement program — find the most accomplished graduates in your class.
          </p>
          <div className="flex items-center justify-center gap-2 text-xs text-slate-400">
            <span className="rounded-full bg-green-100 text-green-700 px-2 py-0.5 font-medium">
              100% Free
            </span>
            <span>·</span>
            <span>Gemini Vision · Google Search · GitHub API</span>
          </div>
        </header>

        {/* ---------------------------------------------------------------- */}
        {/* Upload form                                                       */}
        {/* ---------------------------------------------------------------- */}
        <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
          <UploadForm onSubmit={run} isLoading={isLoading} />
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Pipeline progress (visible while running, before results appear)  */}
        {/* ---------------------------------------------------------------- */}
        {(isLoading || messages.length > 0) && (
          <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6">
            <h2 className="text-sm font-semibold text-slate-700 mb-4 uppercase tracking-wide">
              Pipeline Progress
            </h2>
            <PipelineProgress
              completedStages={completedStages}
              currentStage={currentStage}
              messages={messages}
            />
          </div>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Error state                                                       */}
        {/* ---------------------------------------------------------------- */}
        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Tab bar + content — shown as soon as leaderboard or stats arrive  */}
        {/* ---------------------------------------------------------------- */}
        {hasAnyResults && (
          <div className="space-y-6">
            <Tabs
              tabs={tabs}
              active={activeTab}
              onChange={(id) => setActiveTab(id as TabId)}
            />

            {activeTab === "leaderboard" && results && (
              <Leaderboard results={results} />
            )}

            {activeTab === "leaderboard" && !results && (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-400 text-sm">
                Leaderboard will appear once scoring is complete…
              </div>
            )}

            {activeTab === "dashboard" && stats && (
              <Dashboard stats={stats} isLive={isLoading} />
            )}

            {activeTab === "dashboard" && !stats && (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-400 text-sm">
                Dashboard will appear after LinkedIn results are processed…
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
