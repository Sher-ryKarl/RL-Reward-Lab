import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type ExperimentSummary } from "../api/client";

export function ExperimentListPage() {
  const [exps, setExps] = useState<ExperimentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = async () => {
    setLoading(true);
    try {
      const data = await api.listExperiments();
      setExps(data.items);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    reload();
    const interval = setInterval(reload, 5_000);
    return () => clearInterval(interval);
  }, []);

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

  if (loading && exps.length === 0) {
    return <div className="text-center text-gray-400 py-12">Loading...</div>;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-2">Failed to load experiments.</p>
        <button onClick={reload} className="text-indigo-600 underline text-sm">
          Retry
        </button>
      </div>
    );
  }

  if (exps.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-400 text-lg mb-4">No experiments yet.</p>
        <Link
          to="/new"
          className="bg-indigo-600 text-white px-5 py-2 rounded font-medium hover:bg-indigo-700"
        >
          Create First Experiment
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">Experiments</h2>
        <Link
          to="/new"
          className="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-indigo-700"
        >
          + New
        </Link>
      </div>

      <div className="grid gap-3">
        {exps.map((exp) => (
          <Link
            key={exp.id}
            to={`/experiments/${exp.id}`}
            className="block border rounded-lg p-4 hover:border-indigo-300 hover:shadow-sm bg-white transition"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">{exp.name}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {exp.env_id} · {exp.algo_id} · {exp.total_steps.toLocaleString()} steps
                  · {new Date(exp.created_at).toLocaleDateString()}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={statusBadge(exp.status)}>{exp.status}</span>
                <span className="text-xs text-gray-400">{exp.runs.length} runs</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
