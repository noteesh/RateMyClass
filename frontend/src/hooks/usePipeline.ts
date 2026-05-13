/**
 * usePipeline — custom hook that manages the full pipeline state.
 *
 * Handles:
 *  - Uploading the photo to the backend
 *  - Consuming the streaming response event by event
 *  - Tracking which stages are done, the current active stage, and log messages
 *  - Storing the final leaderboard results ("done" event)
 *  - Storing the class-wide stats ("stats" event) separately so the Dashboard
 *    can render as soon as stats arrive, independently of the full results
 */

import { useState, useCallback } from "react";
import * as api from "../lib/api";
import type { AnalyseResponse, ClassStats, PipelineStage } from "../lib/types";

interface PipelineState {
  isLoading: boolean;
  completedStages: Set<PipelineStage>;
  currentStage: PipelineStage | null;
  messages: string[];
  results: AnalyseResponse | null;
  stats: ClassStats | null;
  error: string | null;
}

export function usePipeline() {
  const [state, setState] = useState<PipelineState>({
    isLoading: false,
    completedStages: new Set(),
    currentStage: null,
    messages: [],
    results: null,
    stats: null,
    error: null,
  });

  const run = useCallback(async (file: File, university: string, year: string) => {
    setState({
      isLoading: true,
      completedStages: new Set(),
      currentStage: null,
      messages: [],
      results: null,
      stats: null,
      error: null,
    });

    try {
      for await (const event of api.analyse(file, {
        university: university || undefined,
        graduationYear: year ? parseInt(year) : undefined,
      })) {
        setState((prev) => {
          const newCompleted = new Set(prev.completedStages);

          // Mark the previous stage complete when a new one starts
          if (prev.currentStage && prev.currentStage !== event.stage) {
            newCompleted.add(prev.currentStage);
          }

          if (event.stage === "done") {
            newCompleted.add("scoring");
            newCompleted.add("stats");
            newCompleted.add("done");
          }

          // Route the data payload to the right state field
          const isStats = event.stage === "stats";
          const isDone = event.stage === "done";

          return {
            ...prev,
            currentStage: isDone ? null : event.stage,
            completedStages: newCompleted,
            messages: [...prev.messages, event.message],
            stats: isStats ? (event.data as ClassStats) : prev.stats,
            results: isDone ? (event.data as AnalyseResponse) : prev.results,
            isLoading: !isDone,
          };
        });
      }
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Unknown error",
      }));
    }
  }, []);

  return { ...state, run };
}
