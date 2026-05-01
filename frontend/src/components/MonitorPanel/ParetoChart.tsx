import ReactECharts from "echarts-for-react";
import type { TrialResult, TrialScore } from "../../api/client";

interface Props {
  trials: TrialResult[];
  paretoFront: TrialResult[];
  nObjectives: number;
  highlightedTrial?: TrialResult | null;
  scores?: TrialScore[];
}

const REWARD_COLORS = [
  "#5470C6", "#91CC75", "#FAC858", "#EE6666", "#73C0DE",
  "#3BA272", "#FC8452", "#9A60B4",
];

function rewardColor(rid: string): string {
  let hash = 0;
  for (let i = 0; i < rid.length; i++) hash = rid.charCodeAt(i) + ((hash << 5) - hash);
  return REWARD_COLORS[Math.abs(hash) % REWARD_COLORS.length];
}

function rewardName(rid: string): string {
  const short: Record<string, string> = {
    R0_sparse: "Sparse", R1_dense: "Dense", R2_pbrs_potential: "PBRS",
    R3_curiosity_rnd: "Curiosity", R4_misleading: "Misleading",
  };
  return short[rid] || rid.substring(0, 8);
}

export function ParetoChart({ trials, paretoFront, nObjectives, highlightedTrial, scores: _scores }: Props) {
  if (nObjectives < 2 || trials.length === 0) {
    return (
      <div className="border rounded p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Pareto Frontier</h3>
        <p className="text-sm text-gray-400">
          Multi-objective optimization not active. Run an HPO experiment to see the Pareto frontier.
        </p>
      </div>
    );
  }

  const paretoSet = new Set(paretoFront.map((t) => t.number));
  const rewardIds = [...new Set(trials.map((t) => t.reward_id))];

  // Legend-separated series per reward_id, with Pareto points highlighted
  const seriesByReward: Record<string, { all: number[][]; pareto: number[][] }> = {};
  for (const rid of rewardIds) {
    seriesByReward[rid] = { all: [], pareto: [] };
  }
  for (const t of trials) {
    if (t.values.length < 2) continue;
    const pt = [t.values[1], t.values[0]]; // X=wall_time, Y=ep_rew_mean
    seriesByReward[t.reward_id].all.push(pt);
    if (paretoSet.has(t.number)) {
      seriesByReward[t.reward_id].pareto.push(pt);
    }
  }

  const scatterSeries = rewardIds.flatMap((rid) => {
    const { all, pareto } = seriesByReward[rid];
    const color = rewardColor(rid);
    const name = rewardName(rid);
    const items: any[] = [];
    if (all.length > 0) {
      items.push({
        name: `${name} (all)`,
        type: "scatter",
        data: all,
        symbolSize: 8,
        itemStyle: { color, opacity: 0.35 },
        legendHoverLink: false,
        silent: true,
      });
    }
    if (pareto.length > 0) {
      items.push({
        name: `${name} (Pareto)`,
        type: "scatter",
        data: pareto,
        symbolSize: 14,
        itemStyle: { color, borderColor: "#333", borderWidth: 1.5 },
        emphasis: { scale: 1.5 },
      });
    }
    return items;
  });

  // Highlighted / recommended trial
  if (highlightedTrial && highlightedTrial.values.length >= 2) {
    scatterSeries.push({
      name: "★ Recommended",
      type: "scatter",
      data: [[highlightedTrial.values[1], highlightedTrial.values[0]]],
      symbolSize: 22,
      symbol: "diamond",
      itemStyle: { color: "#f59e0b", borderColor: "#92400e", borderWidth: 2 },
      emphasis: { scale: 1.3 },
      zlevel: 10,
    });
  }

  // Pareto front connecting line (sorted by O1 descending)
  const paretoLine = paretoFront
    .filter((t) => t.values.length >= 2)
    .sort((a, b) => b.values[0] - a.values[0])
    .map((t) => [t.values[1], t.values[0]]);

  if (paretoLine.length >= 2) {
    scatterSeries.push({
      name: "Pareto front",
      type: "line",
      data: paretoLine,
      smooth: false,
      lineStyle: { color: "#999", type: "dashed", width: 1 },
      symbol: "none",
      silent: true,
    });
  }

  const option = {
    title: {
      text: "Pareto Frontier — Reward vs Speed",
      textStyle: { fontSize: 12, fontWeight: "normal" },
    },
    tooltip: {
      trigger: "item",
      formatter: (p: any) => {
        const d = p.data;
        return `Reward: ${d[1]?.toFixed(1)}<br/>Wall time: ${d[0]?.toFixed(1)}s`;
      },
    },
    legend: {
      type: "scroll",
      bottom: 0,
      textStyle: { fontSize: 10 },
    },
    xAxis: { name: "Wall time (s)", nameLocation: "center", nameGap: 30 },
    yAxis: { name: "Episode Reward", nameLocation: "center", nameGap: 40 },
    grid: { left: 60, right: 20, top: 40, bottom: 60 },
    series: scatterSeries,
  };

  // Second view: convergence_steps vs ep_rew_mean (only if 3 objectives)
  const hasConvergence = nObjectives >= 3 && trials.some((t) => t.values.length >= 3);
  let option2: any = null;
  if (hasConvergence) {
    const convData = trials
      .filter((t) => t.values.length >= 3)
      .map((t) => ({
        value: [t.values[2], t.values[0]],
        reward_id: t.reward_id,
        isPareto: paretoSet.has(t.number),
      }));

    option2 = {
      title: {
        text: "Pareto Frontier — Reward vs Convergence",
        textStyle: { fontSize: 12, fontWeight: "normal" },
      },
      legend: { show: false },
      xAxis: { name: "Convergence steps", nameLocation: "center", nameGap: 30 },
      yAxis: { name: "Episode Reward", nameLocation: "center", nameGap: 40 },
      grid: { left: 60, right: 20, top: 40, bottom: 40 },
      series: [
        {
          type: "scatter",
          data: convData,
          symbolSize: (d: any) => (d.isPareto ? 14 : 7),
          itemStyle: {
            borderColor: (d: any) => (d.isPareto ? "#333" : undefined),
            borderWidth: (d: any) => (d.isPareto ? 1.5 : 0),
            opacity: (d: any) => (d.isPareto ? 1 : 0.4),
            color: (d: any) => rewardColor(d.reward_id),
          },
        },
      ],
      tooltip: {
        trigger: "item",
        formatter: (p: any) => {
          const d = p.data as any;
          return `${rewardName(d.reward_id)}<br/>Reward: ${d.value[1]?.toFixed(1)}<br/>Convergence: ${d.value[0]?.toFixed(0)} steps`;
        },
      },
    };
  }

  return (
    <div className="border rounded p-4 space-y-4">
      <h3 className="text-sm font-semibold text-gray-700">Pareto Frontier</h3>
      <ReactECharts option={option} style={{ height: 320 }} />
      {option2 && <ReactECharts option={option2} style={{ height: 320 }} />}
      <p className="text-xs text-gray-400">
        <strong>Pareto-optimal</strong> trials are highlighted with dark borders. No other trial
        is strictly better on <em>all</em> objectives simultaneously.
      </p>
    </div>
  );
}
