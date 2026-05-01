import ReactEChartsCore from "echarts-for-react";
import type { OptimizationResult } from "../../api/client";

interface Props {
  data: OptimizationResult;
}

const REWARD_COLORS = [
  "#3b82f6", "#ef4444", "#22c55e", "#a855f7", "#f59e0b",
  "#06b6d4", "#ec4899", "#84cc16",
];

export function OptimizationCharts({ data }: Props) {
  if (data.trials.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8 text-sm">
        No trials completed yet.
      </div>
    );
  }

  // Collect all param keys from trials (excluding reward_id — displayed separately)
  const paramKeys = new Set<string>();
  for (const t of data.trials) {
    for (const k of Object.keys(t.params)) {
      if (k !== "reward_id") paramKeys.add(k);
    }
  }
  const dims = [...paramKeys];

  // Per-reward color mapping
  const rewardIds = Object.keys(data.per_reward);
  const rewardColorMap: Record<string, string> = {};
  rewardIds.forEach((rid, i) => {
    rewardColorMap[rid] = REWARD_COLORS[i % REWARD_COLORS.length];
  });

  // ── Scatter: trial number vs value, colored by reward ────────────────
  const scatterOption = {
    tooltip: {
      trigger: "item",
      formatter: (p: { data: number[] }) => {
        const idx = p.data[0] - 1;
        const trial = data.trials[idx];
        if (!trial) return "";
        const params = Object.entries(trial.params)
          .filter(([k]) => k !== "reward_id")
          .map(([k, v]) => `${k}=${v}`)
          .join("<br/>");
        return `Trial ${trial.number}<br/>${trial.reward_id}<br/>Value: ${trial.value.toFixed(4)}<br/>${params}`;
      },
    },
    xAxis: { name: "Trial", type: "value", minInterval: 1 },
    yAxis: { name: "Reward (mean)" },
    series: rewardIds.map((rid) => {
      const trials = data.per_reward[rid]?.trials || [];
      return {
        name: rid,
        type: "scatter",
        data: trials
          .sort((a, b) => a.number - b.number)
          .map((t) => [t.number, t.value]),
        symbolSize: 10,
        itemStyle: { color: rewardColorMap[rid] },
      };
    }),
    legend: {
      data: rewardIds,
      bottom: 0,
      textStyle: { fontSize: 11 },
    },
  };

  // ── Optimization history: curves per reward ──────────────────────────
  const historyOption = {
    tooltip: { trigger: "axis" as const },
    legend: {
      data: rewardIds,
      bottom: 0,
      textStyle: { fontSize: 11 },
    },
    xAxis: { name: "Trial", type: "value", minInterval: 1 },
    yAxis: { name: "Reward (mean)" },
    series: rewardIds.map((rid) => {
      const trials = (data.per_reward[rid]?.trials || [])
        .slice()
        .sort((a, b) => a.number - b.number);
      // Cumulative best-so-far per reward
      const values: [number, number][] = [];
      let best = -Infinity;
      for (const t of trials) {
        if (t.value > best) best = t.value;
        values.push([t.number, best]);
      }
      return {
        name: rid,
        type: "line",
        data: values,
        smooth: true,
        step: "end" as const,
        lineStyle: { color: rewardColorMap[rid], width: 2 },
        itemStyle: { color: rewardColorMap[rid] },
        symbol: "none" as const,
      };
    }),
  };

  // ── Per-reward bar chart: best value per reward ──────────────────────
  const barOption = {
    tooltip: { trigger: "axis" as const },
    xAxis: {
      type: "category" as const,
      data: rewardIds,
      axisLabel: { rotate: 20, fontSize: 10 },
    },
    yAxis: { name: "Best Reward", type: "value" as const },
    series: [
      {
        type: "bar",
        data: rewardIds.map((rid) => ({
          value: data.per_reward[rid]?.best_value || 0,
          itemStyle: { color: rewardColorMap[rid] },
        })),
        label: {
          show: true,
          position: "top",
          formatter: (p: { value: number }) => p.value.toFixed(2),
          fontSize: 10,
        },
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Per-reward best cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {rewardIds.map((rid) => {
          const entry = data.per_reward[rid];
          if (!entry) return null;
          return (
            <div
              key={rid}
              className="border rounded p-3 bg-white"
              style={{ borderLeftColor: rewardColorMap[rid], borderLeftWidth: 4 }}
            >
              <div
                className="text-sm font-semibold"
                style={{ color: rewardColorMap[rid] }}
              >
                {rid}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Best: <span className="font-mono font-semibold">{entry.best_value.toFixed(4)}</span>
                {" · "}{entry.n_trials} trials
              </div>
              <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 mt-2">
                {Object.entries(entry.best_params)
                  .filter(([k]) => k !== "reward_id")
                  .slice(0, 4)
                  .map(([k, v]) => (
                    <span key={k} className="text-xs text-gray-600 truncate">
                      <code className="font-semibold">{k}</code>: {typeof v === "number" ? v.toFixed(6) : String(v)}
                    </span>
                  ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Best value comparison bar */}
      {rewardIds.length > 1 && (
        <div className="border rounded bg-white p-2">
          <p className="text-xs font-semibold text-gray-600 mb-1 px-1">
            Best Reward by Variant
          </p>
          <ReactEChartsCore option={barOption} style={{ height: 250 }} notMerge />
        </div>
      )}

      {/* Optimization history curves */}
      {rewardIds.length > 1 && (
        <div className="border rounded bg-white p-2">
          <p className="text-xs font-semibold text-gray-600 mb-1 px-1">
            Optimization History (best-so-far per reward)
          </p>
          <ReactEChartsCore option={historyOption} style={{ height: 300 }} notMerge />
        </div>
      )}

      {/* Scatter plot */}
      <div className="border rounded bg-white p-2">
        <p className="text-xs font-semibold text-gray-600 mb-1 px-1">
          Trial Reward Scatter (colored by reward)
        </p>
        <ReactEChartsCore option={scatterOption} style={{ height: 280 }} notMerge />
      </div>

      {/* Parallel coordinates */}
      {dims.length >= 2 && (
        <div className="border rounded bg-white p-2">
          <p className="text-xs font-semibold text-gray-600 mb-1 px-1">
            Parallel Coordinates
          </p>
          <ReactEChartsCore
            option={buildParallel(data, dims)}
            style={{ height: 300 }}
            notMerge
          />
        </div>
      )}

      {/* Trial history table */}
      <div className="border rounded bg-white overflow-auto max-h-80">
        <table className="w-full text-xs">
          <thead className="bg-gray-100 sticky top-0">
            <tr>
              <th className="px-2 py-1 text-left">#</th>
              <th className="px-2 py-1 text-left">Reward</th>
              <th className="px-2 py-1 text-left">Value</th>
              {dims.map((d) => (
                <th key={d} className="px-2 py-1 text-left">
                  {d}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[...data.trials]
              .sort((a, b) => b.value - a.value)
              .map((t) => (
                <tr
                  key={t.number}
                  className="hover:bg-gray-50"
                  style={{
                    background:
                      t.value === data.per_reward[t.reward_id]?.best_value
                        ? `${rewardColorMap[t.reward_id] || "#ddd"}10`
                        : undefined,
                  }}
                >
                  <td className="px-2 py-1">{t.number}</td>
                  <td className="px-2 py-1">
                    <span
                      className="px-1.5 py-0.5 rounded text-xs"
                      style={{
                        background: rewardColorMap[t.reward_id] || "#ccc",
                        color: "#fff",
                      }}
                    >
                      {t.reward_id}
                    </span>
                  </td>
                  <td className="px-2 py-1 font-mono">{t.value.toFixed(4)}</td>
                  {dims.map((d) => (
                    <td key={d} className="px-2 py-1 font-mono">
                      {String(t.params[d] ?? "-")}
                    </td>
                  ))}
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function buildParallel(data: OptimizationResult, dims: string[]) {
  const pcDims = [
    ...dims.map((d) => ({
      name: d,
      type: "value" as const,
    })),
    { name: "ep_rew_mean", type: "value" as const },
  ];

  const pcData = data.trials.map((t) => {
    const row: number[] = [];
    for (const d of dims) {
      const v = t.params[d];
      row.push(typeof v === "number" ? v : 0);
    }
    row.push(t.value);
    return row;
  });

  return {
    tooltip: {},
    parallelAxis: pcDims.map((d) => ({ dim: pcDims.indexOf(d), name: d.name })),
    parallel: {
      left: "5%",
      right: "5%",
      top: "15%",
      bottom: "10%",
      parallelAxisDefault: {
        type: "value",
        nameLocation: "end",
      },
    },
    series: [
      {
        type: "parallel",
        lineStyle: { width: 2, color: "#6366f1", opacity: 0.6 },
        data: pcData,
      },
    ],
  };
}
