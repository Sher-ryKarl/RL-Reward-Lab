import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, type ExperimentSummary } from "../api/client";
import { MonitorPanel } from "../components/MonitorPanel/MonitorPanel";
import { ReplayViewer } from "../components/ReplayViewer/ReplayViewer";

export function ExperimentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [exp, setExp] = useState<ExperimentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeRun, setActiveRun] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const poll = () => {
      api
        .getExperiment(id)
        .then(setExp)
        .catch((e) => setError(String(e)))
        .finally(() => setLoading(false));
    };
    poll();
    const interval = setInterval(poll, 3_000);
    return () => clearInterval(interval);
  }, [id]);

  if (loading) {
    return <div className="text-center text-gray-400 py-12">Loading...</div>;
  }

  if (error || !exp) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error || "Experiment not found"}</p>
        <Link to="/" className="text-indigo-600 underline text-sm mt-2 block">
          Back to list
        </Link>
      </div>
    );
  }

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      pending: "bg-gray-100 text-gray-600",
      running: "bg-blue-100 text-blue-700",
      done: "bg-green-100 text-green-700",
      failed: "bg-red-100 text-red-700",
      cancelled: "bg-yellow-100 text-yellow-700",
    };
    return `px-2 py-0.5 rounded-full text-xs font-medium ${map[status] || map.pending}`;
  };

  return (
    <div className="space-y-6">
      <div>
        <Link to="/" className="text-sm text-indigo-600 hover:underline">
          ← Back
        </Link>
        <h2 className="text-xl font-semibold text-gray-800 mt-1">{exp.name}</h2>
        <div className="text-sm text-gray-500 flex gap-4 mt-1">
          <span>{exp.env_id}</span>
          <span>{exp.algo_id}</span>
          <span>{exp.total_steps.toLocaleString()} steps</span>
          <span className={statusBadge(exp.status)}>{exp.status}</span>
        </div>
      </div>

      {/* Run selector */}
      <div className="flex flex-wrap gap-2">
        {exp.runs.map((run) => (
          <button
            key={run.id}
            onClick={() => setActiveRun(run.id)}
            className={`px-3 py-1.5 rounded text-sm font-medium border transition ${
              activeRun === run.id
                ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                : "border-gray-200 hover:border-gray-300"
            }`}
          >
            {run.reward_id} (seed {run.seed})
            <span className={`ml-1.5 ${statusBadge(run.status)}`}>{run.status}</span>
          </button>
        ))}
      </div>

      {/* Monitor / Replay for active run */}
      {activeRun ? (
        <>
          <MonitorPanel runId={activeRun} />
          <ReplayViewer runId={activeRun} />
        </>
      ) : (
        <div className="text-center text-gray-400 py-8 border rounded">
          Select a run to monitor
        </div>
      )}
    </div>
  );
}
