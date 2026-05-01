import { useEffect, useRef, useState } from "react";
import { subscribeRunStream } from "../api/stream";
import type { MetricEvent } from "../api/client";

interface SeriesData {
  step: number[];
  ep_rew_mean: number[];
}

const MAX_POINTS = 500;
const THROTTLE_MS = 250;

function _downsample(step: number[], values: number[]): { step: number[]; values: number[] } {
  const factor = 2;
  const newStep: number[] = [];
  const newValues: number[] = [];
  for (let i = 0; i < step.length; i += factor) {
    newStep.push(step[i]);
    newValues.push(values[i]);
  }
  return { step: newStep, values: newValues };
}

export function useRunStream(runId: string | null) {
  const [connected, setConnected] = useState(false);
  const [latest, setLatest] = useState<MetricEvent | null>(null);
  const seriesRef = useRef<Map<string, SeriesData>>(new Map());
  const [seriesMap, setSeriesMap] = useState<Map<string, SeriesData>>(
    new Map(),
  );
  const lastFlushRef = useRef<number>(0);
  const pendingRef = useRef<boolean>(false);

  useEffect(() => {
    if (!runId) return;
    seriesRef.current.clear();
    setSeriesMap(new Map());
    setLatest(null);
    lastFlushRef.current = 0;
    pendingRef.current = false;

    const _flush = () => {
      pendingRef.current = false;
      setSeriesMap(new Map(seriesRef.current));
    };

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

        // Downsample when exceeding threshold (keep every 2nd point)
        if (s.step.length > MAX_POINTS * 2) {
          const ds = _downsample(s.step, s.ep_rew_mean);
          s.step = ds.step;
          s.ep_rew_mean = ds.values;
        }

        seriesRef.current.set(rid, s);

        const now = performance.now();
        if (now - lastFlushRef.current >= THROTTLE_MS) {
          lastFlushRef.current = now;
          pendingRef.current = false;
          setSeriesMap(new Map(seriesRef.current));
        } else {
          pendingRef.current = true;
        }
      },
      setConnected,
    );

    return () => {
      ctrl.abort();
      if (pendingRef.current) {
        _flush();
      }
    };
  }, [runId]);

  return { connected, latest, seriesMap };
}

/** Poll historical metrics when a run is not actively streaming. */
export function useRunMetrics(runId: string | null) {
  const [metrics, setMetrics] = useState<MetricEvent[]>([]);

  useEffect(() => {
    if (!runId) return;
    fetch(`/api/v1/runs/${runId}`)
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
