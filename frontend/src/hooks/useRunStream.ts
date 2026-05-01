import { useEffect, useRef, useState } from "react";
import { subscribeRunStream } from "../api/stream";
import type { MetricEvent } from "../api/client";

interface SeriesData {
  step: number[];
  ep_rew_mean: number[];
}

export function useRunStream(runId: string | null) {
  const [connected, setConnected] = useState(false);
  const [latest, setLatest] = useState<MetricEvent | null>(null);
  const seriesRef = useRef<Map<string, SeriesData>>(new Map());
  const [seriesMap, setSeriesMap] = useState<Map<string, SeriesData>>(
    new Map(),
  );

  useEffect(() => {
    if (!runId) return;
    seriesRef.current.clear();
    setSeriesMap(new Map());
    setLatest(null);

    const ctrl = subscribeRunStream(
      runId,
      (event) => {
        setLatest(event);
        const rid = event.reward_id || runId;
        const s = seriesRef.current.get(rid) || {
          step: [],
          ep_rew_mean: [],
        };
        s.step.push(event.step);
        s.ep_rew_mean.push(event.metrics.ep_rew_mean ?? 0);
        seriesRef.current.set(rid, s);
        setSeriesMap(new Map(seriesRef.current));
      },
      setConnected,
    );

    return () => ctrl.abort();
  }, [runId]);

  return { connected, latest, seriesMap };
}

/** Poll historical metrics when a run is not actively streaming. */
export function useRunMetrics(runId: string | null) {
  const [metrics, setMetrics] = useState<MetricEvent[]>([]);

  useEffect(() => {
    if (!runId) return;
    fetch(`http://localhost:8000/api/v1/runs/${runId}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.final_metrics) {
          setMetrics([
            {
              run_id: runId,
              reward_id: data.reward_id,
              step: 0,
              wall_time: 0,
              metrics: data.final_metrics,
              components: null,
            },
          ]);
        }
      })
      .catch(() => setMetrics([]));
  }, [runId]);

  return metrics;
}
