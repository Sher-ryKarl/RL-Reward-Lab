import ReactECharts from "echarts-for-react";

interface SeriesEntry {
  step: number[];
  ep_rew_mean: number[];
}

interface Props {
  seriesMap: Map<string, SeriesEntry>;
}

const COLORS = ["#94a3b8", "#3b82f6", "#22c55e", "#a855f7", "#ef4444"];

export function LearningCurveChart({ seriesMap }: Props) {
  const names = Array.from(seriesMap.keys());
  const colorMap: Record<string, string> = {};
  names.forEach((n, i) => (colorMap[n] = COLORS[i % COLORS.length]));

  const option = {
    title: { text: "Learning Curve (ep_rew_mean)", left: "center", textStyle: { fontSize: 14 } },
    tooltip: { trigger: "axis" as const },
    legend: { data: names, bottom: 0 },
    xAxis: { type: "value" as const, name: "Step", nameLocation: "center" as const, nameGap: 30 },
    yAxis: { type: "value" as const, name: "Episode Reward Mean" },
    dataZoom: [{ type: "slider" as const }, { type: "inside" as const }],
    series: names.map((name) => {
      const s = seriesMap.get(name)!;
      return {
        name,
        type: "line",
        data: s.step.map((x, i) => [x, s.ep_rew_mean[i]]),
        smooth: true,
        lineStyle: { color: colorMap[name], width: 2 },
        itemStyle: { color: colorMap[name] },
        symbol: "none" as const,
      };
    }),
  };

  return <ReactECharts option={option} style={{ height: 400 }} />;
}
