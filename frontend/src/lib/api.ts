/**
 * API client — all backend communication lives here.
 *
 * The analyse() function sends the photo + metadata and returns an
 * async generator that yields PipelineEvent objects as the backend
 * streams progress updates line by line.
 */

import type { PipelineEvent } from "./types";

/**
 * Upload a commencement program photo and stream back pipeline progress events.
 *
 * Usage:
 *   for await (const event of api.analyse(file, { university: "UIUC" })) {
 *     if (event.stage === "done") setResults(event.data);
 *   }
 */
export async function* analyse(
  file: File,
  options: { university?: string; graduationYear?: number; skipGithub?: boolean } = {}
): AsyncGenerator<PipelineEvent> {
  const form = new FormData();
  form.append("file", file);
  if (options.university) form.append("university", options.university);
  if (options.graduationYear) form.append("graduation_year", String(options.graduationYear));
  if (options.skipGithub) form.append("skip_github", "true");

  const response = await fetch("/api/analyse", { method: "POST", body: form });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text}`);
  }

  if (!response.body) throw new Error("No response body from server");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    // Keep the last (potentially incomplete) line in the buffer
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.trim()) {
        try {
          yield JSON.parse(line) as PipelineEvent;
        } catch {
          // Ignore malformed lines
        }
      }
    }
  }
}
