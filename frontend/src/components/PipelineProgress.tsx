/**
 * PipelineProgress — shows a live status bar as each backend stage completes.
 * Each stage lights up green when done, pulses while in progress.
 */

import { CheckCircle, Circle, Loader2 } from "lucide-react";
import type { PipelineStage } from "../lib/types";

const STAGES: { key: PipelineStage; label: string }[] = [
  { key: "ocr",      label: "Reading Photo" },
  { key: "linkedin", label: "LinkedIn Search" },
  { key: "github",   label: "GitHub Signals" },
  { key: "scoring",  label: "AI Scoring" },
  { key: "stats",    label: "Dashboard" },
  { key: "done",     label: "Complete" },
];

interface Props {
  completedStages: Set<PipelineStage>;
  currentStage: PipelineStage | null;
  messages: string[];
}

export default function PipelineProgress({ completedStages, currentStage, messages }: Props) {
  return (
    <div className="space-y-4">
      {/* Stage tracker */}
      <div className="flex items-center justify-between">
        {STAGES.map((stage, i) => {
          const done = completedStages.has(stage.key);
          const active = currentStage === stage.key;

          return (
            <div key={stage.key} className="flex items-center flex-1">
              <div className="flex flex-col items-center gap-1">
                {done ? (
                  <CheckCircle className="h-6 w-6 text-green-500" />
                ) : active ? (
                  <Loader2 className="h-6 w-6 text-indigo-500 animate-spin" />
                ) : (
                  <Circle className="h-6 w-6 text-slate-300" />
                )}
                <span className={`text-xs font-medium ${done ? "text-green-600" : active ? "text-indigo-600" : "text-slate-400"}`}>
                  {stage.label}
                </span>
              </div>
              {/* Connector line */}
              {i < STAGES.length - 1 && (
                <div className={`flex-1 h-0.5 mx-2 mb-4 ${done ? "bg-green-300" : "bg-slate-200"}`} />
              )}
            </div>
          );
        })}
      </div>

      {/* Live log */}
      <div className="rounded-xl bg-slate-900 text-slate-300 text-xs font-mono p-4 max-h-32 overflow-y-auto space-y-1">
        {messages.length === 0 ? (
          <p className="text-slate-500">Starting pipeline…</p>
        ) : (
          messages.map((msg, i) => (
            <p key={i}>
              <span className="text-indigo-400">→</span> {msg}
            </p>
          ))
        )}
      </div>
    </div>
  );
}
