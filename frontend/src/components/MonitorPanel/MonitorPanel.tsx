import { useRunStream } from "../../hooks/useRunStream";
import { LearningCurveChart } from "./LearningCurveChart";
import { HealthCard } from "./HealthCard";

interface Props {
  runId: string;
}

export function MonitorPanel({ runId }: Props) {
  const { connected, latest, seriesMap } = useRunStream(runId);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-semibold text-gray-800">
          Run: <code className="text-indigo-600">{runId}</code>
        </h2>
        <span
          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
            connected
              ? "bg-green-100 text-green-700"
              : "bg-yellow-100 text-yellow-700"
          }`}
        >
          {connected ? "Live" : "Reconnecting..."}
        </span>
      </div>
      <LearningCurveChart seriesMap={seriesMap} />
      <HealthCard metrics={latest?.metrics ?? null} />
    </div>
  );
}
