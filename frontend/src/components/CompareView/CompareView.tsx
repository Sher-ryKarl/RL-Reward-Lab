import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { api, type ExperimentSummary } from "../../api/client";
import { MultiRunChart } from "../MonitorPanel/MultiRunChart";

export function CompareView() {
  const [searchParams] = useSearchParams();
  const [exps, setExps] = useState<ExperimentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const ids = searchParams.get("ids")?.split(",").filter(Boolean) || [];

  useEffect(() => {
    if (ids.length === 0) {
      setLoading(false);
      return;
    }
    Promise.all(ids.map((id) => api.getExperiment(id).catch(() => null)))
      .then((results) => {
        setExps(results.filter(Boolean) as ExperimentSummary[]);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [searchParams]);

  if (loading) {
    return <div className="text-center text-gray-400 py-12">Loading...</div>;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (ids.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-400 text-lg mb-2">No experiments selected for comparison.</p>
        <p className="text-gray-400 text-sm mb-6">
          Go to the experiment list, select 2+ experiments and click "Compare".
        </p>
        <Link
          to="/"
          className="bg-indigo-600 text-white px-5 py-2 rounded font-medium hover:bg-indigo-700"
        >
          Back to Experiments
        </Link>
      </div>
    );
  }

  // Flatten all runs across selected experiments
  const allRunIds: string[] = [];
  const allLabels: string[] = [];
  for (const exp of exps) {
    for (const run of exp.runs) {
      allRunIds.push(run.id);
      allLabels.push(`${exp.name} / ${run.reward_id} (s${run.seed})`);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">
          Compare Experiments ({exps.length})
        </h2>
        <Link to="/" className="text-sm text-indigo-600 hover:underline">
          ← Back
        </Link>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {exps.map((exp) => (
          <div key={exp.id} className="border rounded-lg p-3 bg-white">
            <div className="font-medium text-sm">{exp.name}</div>
            <div className="text-xs text-gray-500 mt-1">
              {exp.env_id} · {exp.algo_id} · {exp.runs.length} runs
            </div>
            <div className="flex flex-wrap gap-1 mt-2">
              {exp.runs.map((r) => (
                <span
                  key={r.id}
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    r.status === "done"
                      ? "bg-green-100 text-green-700"
                      : r.status === "running"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {r.reward_id} (s{r.seed})
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Multi-run comparison chart */}
      {allRunIds.length > 0 && (
        <MultiRunChart runIds={allRunIds} labels={allLabels} />
      )}
    </div>
  );
}
