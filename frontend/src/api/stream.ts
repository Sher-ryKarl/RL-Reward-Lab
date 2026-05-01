/**
 * EventSource wrapper for SSE metric streaming.
 * Auto-reconnects on connection loss (browser EventSource built-in).
 */

import type { MetricEvent } from "./client";

type MetricHandler = (event: MetricEvent) => void;
type StatusHandler = (connected: boolean) => void;

export function subscribeRunStream(
  runId: string,
  onMetric: MetricHandler,
  onStatus?: StatusHandler,
): AbortController {
  const controller = new AbortController();
  const url = `/api/v1/runs/${runId}/stream`;

  // Small delay so the caller can set up UI state
  setTimeout(() => {
    if (controller.signal.aborted) return;

    const es = new EventSource(url);

    es.addEventListener("metric", (e: MessageEvent) => {
      try {
        const data: MetricEvent = JSON.parse(e.data);
        onMetric(data);
      } catch {
        // skip malformed events
      }
    });

    es.addEventListener("ping", () => {
      onStatus?.(true);
    });

    es.addEventListener("open", () => onStatus?.(true));
    es.addEventListener("error", () => {
      onStatus?.(false);
      // EventSource auto-reconnects; if it fails permanently, abort
    });

    controller.signal.addEventListener("abort", () => {
      es.close();
    });
  }, 0);

  return controller;
}
