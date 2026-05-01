import { useEffect, useRef, useState } from "react";
import ReactECharts from "echarts-for-react";
import { useRunStream } from "../../hooks/useRunStream";

interface Props {
  runIds: string[];
  labels?: string[];
}

const COLORS = [
  "#3b82f6", "#ef4444", "#22c55e", "#a855f7", "#f59e0b",
  "#06b6d4", "#ec4899", "#84cc16",
];

export function MultiRunChart({ runIds, labels }: Props) {
  // We need multiple SSE streams — use a map of runId → series data
  const [seriesData, setSeriesData] = useState<
    Record<string, { step: number[]; ep_rew_mean: number[] }>
  >({});

  const instanceRef = useRef<any>(null);

  return (
    <div className="border rounded p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        Reward Comparison — {runIds.length} runs
      </h3>
      {runIds.map((rid) => (
        <SingleRunListener
          key={rid}
          runId={rid}
          onUpdate={(data) =>
            setSeriesData((prev) => ({ ...prev, [rid]: data }))
          }
        />
      ))}
      <ReactECharts
        ref={instanceRef}
        option={buildOption(runIds, labels || runIds, seriesData)}
        style={{ height: 400 }}
      />
    </div>
  );
}

/** Hidden component that subscribes to one run's SSE stream and reports data upward. */
function SingleRunListener({
  runId,
  onUpdate,
}: {
  runId: string;
  onUpdate: (data: { step: number[]; ep_rew_mean: number[] }) => void;
}) {
  const { seriesMap } = useRunStream(runId);
  useEffect(() => {
    const entry = seriesMap.get(runId);
    if (entry) onUpdate(entry);
  }, [seriesMap, runId, onUpdate]);
  return null;
}

function buildOption(
  runIds: string[],
  displayNames: string[],
  data: Record<string, { step: number[]; ep_rew_mean: number[] }>
) {
  return {
    title: {
      text: "Learning Curves (ep_rew_mean)",
      left: "center",
      textStyle: { fontSize: 14 },
    },
    tooltip: { trigger: "axis" as const },
    legend: { data: displayNames, bottom: 0 },
    xAxis: {
      type: "value" as const,
      name: "Step",
      nameLocation: "center" as const,
      nameGap: 30,
    },
    yAxis: { type: "value" as const, name: "Episode Reward Mean" },
    dataZoom: [{ type: "slider" as const }, { type: "inside" as const }],
    series: runIds.map((rid, i) => {
      const s = data[rid];
      return {
        name: displayNames[i] || rid,
        type: "line",
        data: s ? s.step.map((x, j) => [x, s.ep_rew_mean[j]]) : [],
        smooth: true,
        lineStyle: { color: COLORS[i % COLORS.length], width: 2 },
        itemStyle: { color: COLORS[i % COLORS.length] },
        symbol: "none" as const,
      };
    }),
  };
}
