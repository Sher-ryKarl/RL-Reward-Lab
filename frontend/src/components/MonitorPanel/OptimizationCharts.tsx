import ReactEChartsCore from "echarts-for-react";
import type { OptimizationResult } from "../../api/client";

interface Props {
  data: OptimizationResult;
}

export function OptimizationCharts({ data }: Props) {
  if (data.trials.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8 text-sm">
        No trials completed yet.
      </div>
    );
  }

  // Collect all param keys from trials
  const paramKeys = new Set<string>();
  for (const t of data.trials) {
    for (const k of Object.keys(t.params)) {
      paramKeys.add(k);
    }
  }
  const dims = [...paramKeys];

  // ── Scatter: trial number vs value ──────────────────────────────────
  const scatterOption = {
    tooltip: {
      trigger: "item",
      formatter: (p: { data: number[] }) => {
        const trial = data.trials[p.data[0] - 1];
        if (!trial) return "";
        const params = Object.entries(trial.params)
          .map(([k, v]) => `${k}=${v}`)
          .join("<br/>");
        return `Trial ${trial.number}<br/>Value: ${trial.value.toFixed(4)}<br/>${params}`;
      },
    },
    xAxis: { name: "Trial", type: "value", minInterval: 1 },
    yAxis: { name: "Reward (mean)" },
    series: [
      {
        type: "scatter",
        data: data.trials.map((t) => [t.number, t.value]),
        symbolSize: 12,
        itemStyle: { color: "#6366f1" },
      },
    ],
  };

  // ── Parallel coordinates ────────────────────────────────────────────
  // Build dimensions: each param + value
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

  const pcOption = {
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

  // ── Best params highlight ───────────────────────────────────────────
  const bestTrial = data.best_value != null ? data.trials.find((t) => t.value === data.best_value) : null;

  return (
    <div className="space-y-6">
      {/* Best result card */}
      {bestTrial && (
        <div className="bg-green-50 border border-green-300 rounded p-4">
          <p className="text-sm font-semibold text-green-800 mb-2">
            Best Trial (#{bestTrial.number}) — Reward: {bestTrial.value.toFixed(4)}
          </p>
          <div className="grid grid-cols-2 gap-1 text-xs text-green-700">
            {Object.entries(bestTrial.params).map(([k, v]) => (
              <span key={k}>
                <code className="font-semibold">{k}</code>: {String(v)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Scatter plot */}
      <div className="border rounded bg-white p-2">
        <p className="text-xs font-semibold text-gray-600 mb-1 px-1">
          Trial Reward Scatter
        </p>
        <ReactEChartsCore option={scatterOption} style={{ height: 220 }} notMerge />
      </div>

      {/* Parallel coordinates */}
      {dims.length >= 2 && (
        <div className="border rounded bg-white p-2">
          <p className="text-xs font-semibold text-gray-600 mb-1 px-1">
            Parallel Coordinates
          </p>
          <ReactEChartsCore option={pcOption} style={{ height: 300 }} notMerge />
        </div>
      )}

      {/* Trial history table */}
      <div className="border rounded bg-white overflow-auto max-h-64">
        <table className="w-full text-xs">
          <thead className="bg-gray-100 sticky top-0">
            <tr>
              <th className="px-2 py-1 text-left">#</th>
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
                  className={
                    t.value === data.best_value
                      ? "bg-green-50 font-semibold"
                      : "hover:bg-gray-50"
                  }
                >
                  <td className="px-2 py-1">{t.number}</td>
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
