import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api, type ExperimentSummary, type OptimizationResult } from "../api/client";
import { MonitorPanel } from "../components/MonitorPanel/MonitorPanel";
import { MultiRunChart } from "../components/MonitorPanel/MultiRunChart";
import { ReplayViewer } from "../components/ReplayViewer/ReplayViewer";
import { OptimizationCharts } from "../components/MonitorPanel/OptimizationCharts";

export function ExperimentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [exp, setExp] = useState<ExperimentSummary | null>(null);
  const [optResult, setOptResult] = useState<OptimizationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeRun, setActiveRun] = useState<string | null>(null);
  const [compareMode, setCompareMode] = useState(false);
  const [collectingFor, setCollectingFor] = useState<string | null>(null);
  const [demoN_episodes, setDemoNEpisodes] = useState(5);
  const [collectMsg, setCollectMsg] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    const poll = () => {
      Promise.all([
        api.getExperiment(id),
        api.getOptimization(id).catch(() => null),
      ])
        .then(([expData, optData]) => {
          setExp(expData);
          setOptResult(optData);
        })
        .catch((e) => setError(String(e)))
        .finally(() => setLoading(false));
    };
    poll();
    const interval = setInterval(poll, 3_000);
    return () => clearInterval(interval);
  }, [id]);

  const collectDemo = async (runId: string) => {
    if (!exp) return;
    const run = exp.runs.find((r) => r.id === runId);
    if (!run) return;
    setCollectMsg(null);
    try {
      await api.createDemo({
        name: `${exp.name} — ${run.reward_id} demo`,
        env_id: exp.env_id,
        source_run_id: runId,
        n_episodes: demoN_episodes,
        min_timesteps: 2000,
      });
      setCollectMsg(`Demo collected! Go to Demos page to view.`);
      setCollectingFor(null);
    } catch (e) {
      setCollectMsg(`Failed: ${e}`);
    }
  };

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
        <div className="flex items-center justify-between">
          <Link to="/" className="text-sm text-indigo-600 hover:underline">
            ← Back
          </Link>
          <button
            onClick={() =>
              navigate(
                `/new?env_id=${exp.env_id}&algo=${exp.algo_id}`
              )
            }
            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
          >
            Clone & Re-run
          </button>
        </div>
        <h2 className="text-xl font-semibold text-gray-800 mt-1">{exp.name}</h2>
        <div className="text-sm text-gray-500 flex gap-4 mt-1">
          <span>{exp.env_id}</span>
          <span>{exp.algo_id}</span>
          <span>{exp.total_steps.toLocaleString()} steps</span>
          <span className={statusBadge(exp.status)}>{exp.status}</span>
        </div>
      </div>

      {/* Collect demo message */}
      {collectMsg && (
        <div
          className={`border rounded p-3 text-sm ${
            collectMsg.startsWith("Failed")
              ? "bg-red-50 border-red-300 text-red-700"
              : "bg-green-50 border-green-300 text-green-700"
          }`}
        >
          {collectMsg}
          {collectMsg.startsWith("Demo collected") && (
            <Link to="/demos" className="ml-2 underline font-medium">
              View Demos →
            </Link>
          )}
          <button
            onClick={() => setCollectMsg(null)}
            className="ml-2 text-xs underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Run selector */}
      <div className="flex flex-wrap items-center gap-2">
        {exp.runs.map((run) => {
          const isDone = run.status === "done";
          const isCollecting = collectingFor === run.id;
          return (
            <div key={run.id} className="flex items-center gap-1">
              <button
                onClick={() => { setActiveRun(run.id); setCompareMode(false); }}
                className={`px-3 py-1.5 rounded text-sm font-medium border transition ${
                  activeRun === run.id && !compareMode
                    ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                {run.reward_id} (seed {run.seed})
                <span className={`ml-1.5 ${statusBadge(run.status)}`}>{run.status}</span>
              </button>
              {isDone && (
                isCollecting ? (
                  <div className="border rounded p-1 bg-white shadow-sm flex items-center gap-1">
                    <input
                      type="number"
                      value={demoN_episodes}
                      onChange={(e) => setDemoNEpisodes(Number(e.target.value))}
                      min={1}
                      max={50}
                      className="w-12 text-xs border rounded px-1 py-0.5"
                      placeholder="eps"
                    />
                    <button
                      onClick={() => collectDemo(run.id)}
                      className="px-2 py-0.5 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Collect
                    </button>
                    <button
                      onClick={() => setCollectingFor(null)}
                      className="px-1 text-xs text-gray-400 hover:text-gray-600"
                    >
                      ×
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setCollectingFor(run.id)}
                    className="px-2 py-0.5 text-xs border border-green-200 text-green-700 rounded hover:bg-green-50"
                    title="Collect expert demo from this run"
                  >
                    +Demo
                  </button>
                )
              )}
            </div>
          );
        })}
        {exp.runs.length > 1 && (
          <button
            onClick={() => { setCompareMode(!compareMode); setActiveRun(null); }}
            className={`px-3 py-1.5 rounded text-sm font-medium border transition ${
              compareMode
                ? "border-green-500 bg-green-50 text-green-700"
                : "border-gray-200 hover:border-gray-300"
            }`}
          >
            Compare All ({exp.runs.length})
          </button>
        )}
      </div>

      {/* Multi-run comparison chart (v0.6) */}
      {compareMode && exp.runs.length > 1 && (
        <MultiRunChart
          runIds={exp.runs.map((r) => r.id)}
          labels={exp.runs.map((r) => `${r.reward_id} (s${r.seed})`)}
        />
      )}

      {/* Optimization results (v0.2) */}
      {optResult && optResult.trials.length > 0 && (
        <div className="border border-purple-200 rounded p-4 bg-purple-50/50">
          <h3 className="text-sm font-semibold text-purple-800 mb-3">
            Optuna Hyperparameter Search — {optResult.n_trials} trials
          </h3>
          <OptimizationCharts data={optResult} />
        </div>
      )}

      {/* Monitor / Replay for active run */}
      {activeRun ? (
        <>
          <MonitorPanel runId={activeRun} />
          <ReplayViewer
            runId={activeRun}
            runStatus={exp.runs.find((r) => r.id === activeRun)?.status}
          />
        </>
      ) : (
        <div className="text-center text-gray-400 py-8 border rounded">
          Select a run to monitor
        </div>
      )}
    </div>
  );
}
