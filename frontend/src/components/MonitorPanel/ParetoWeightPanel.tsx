import { useState, useEffect, useCallback } from "react";
import { api, type OptimizationResult, type ParetoRecommendResponse, type ConstraintClause } from "../../api/client";

interface Props {
  data: OptimizationResult;
  onRecommend: (rec: ParetoRecommendResponse) => void;
}

const OBJ_LABELS: Record<number, string[]> = {
  2: ["ep_rew_mean", "wall_time"],
  3: ["ep_rew_mean", "wall_time", "convergence_steps"],
};

const OBJ_DISPLAY: Record<string, string> = {
  ep_rew_mean: "Final Reward",
  wall_time: "Training Speed",
  convergence_steps: "Convergence Speed",
};

const ALLOWED_OPS = ["<", "<=", ">", ">="] as const;

export function ParetoWeightPanel({ data, onRecommend }: Props) {
  const nObj = Math.min(data.n_objectives, 3);
  const keys = OBJ_LABELS[nObj] || ["ep_rew_mean"];
  const [weights, setWeights] = useState<number[]>(() => keys.map(() => 1 / keys.length));
  const [constraints, setConstraints] = useState<ConstraintClause[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ParetoRecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Auto-request on weight/constraint change (debounced)
  const fetchRecommend = useCallback(async () => {
    if (data.trials.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const normalWeights = [...weights];
      const sum = normalWeights.reduce((a, b) => a + b, 0);
      for (let i = 0; i < normalWeights.length; i++) {
        normalWeights[i] = sum > 0 ? normalWeights[i] / sum : 1 / normalWeights.length;
      }
      const res = await api.recommendPareto(data.experiment_id, {
        weights: normalWeights,
        constraints,
      });
      setResult(res);
      onRecommend(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [data.experiment_id, data.trials.length, weights, constraints, onRecommend]);

  useEffect(() => {
    const t = setTimeout(fetchRecommend, 300);
    return () => clearTimeout(t);
  }, [fetchRecommend]);

  const handleWeight = (i: number, val: number) => {
    setWeights((prev) => {
      const next = [...prev];
      next[i] = val;
      return next;
    });
  };

  const addConstraint = () => {
    setConstraints((prev) => [...prev, { objective: keys[0], op: "<", value: 0 }]);
  };

  const removeConstraint = (i: number) => {
    setConstraints((prev) => prev.filter((_, idx) => idx !== i));
  };

  const updateConstraint = (i: number, field: keyof ConstraintClause, val: string | number) => {
    setConstraints((prev) => {
      const next = [...prev];
      next[i] = { ...next[i], [field]: val };
      return next;
    });
  };

  const rec = result?.recommended;

  return (
    <div className="border rounded p-4 space-y-4 bg-white">
      <h3 className="text-sm font-semibold text-gray-700">Pareto Decision Assistant</h3>

      {/* Weight sliders */}
      <div>
        <p className="text-xs text-gray-500 mb-2">Weights (drag to adjust preference):</p>
        {keys.map((k, i) => (
          <div key={k} className="flex items-center gap-3 mb-1.5">
            <span className="text-xs w-28 text-gray-600">{OBJ_DISPLAY[k] || k}</span>
            <span className="text-xs w-6 text-right text-gray-400">
              {weights[i].toFixed(1)}
            </span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={weights[i]}
              onChange={(e) => handleWeight(i, parseFloat(e.target.value))}
              className="flex-1 h-1.5 accent-indigo-600 cursor-pointer"
            />
          </div>
        ))}
      </div>

      {/* Constraints */}
      <div>
        <p className="text-xs text-gray-500 mb-1">Constraints (optional):</p>
        {constraints.map((c, i) => (
          <div key={i} className="flex items-center gap-1.5 mb-1">
            <select
              value={c.objective}
              onChange={(e) => updateConstraint(i, "objective", e.target.value)}
              className="border rounded px-1.5 py-0.5 text-xs"
            >
              {keys.map((k) => (
                <option key={k} value={k}>{OBJ_DISPLAY[k] || k}</option>
              ))}
            </select>
            <select
              value={c.op}
              onChange={(e) => updateConstraint(i, "op", e.target.value)}
              className="border rounded px-1.5 py-0.5 text-xs"
            >
              {ALLOWED_OPS.map((op) => (
                <option key={op} value={op}>{op}</option>
              ))}
            </select>
            <input
              type="number"
              value={c.value}
              onChange={(e) => updateConstraint(i, "value", parseFloat(e.target.value) || 0)}
              className="border rounded px-1.5 py-0.5 text-xs w-20"
            />
            <button
              onClick={() => removeConstraint(i)}
              className="text-red-400 hover:text-red-600 text-xs px-1"
            >
              ✕
            </button>
          </div>
        ))}
        <button
          onClick={addConstraint}
          className="text-xs text-indigo-600 hover:underline"
        >
          + Add Constraint
        </button>
      </div>

      {/* Loading / Error */}
      {loading && <p className="text-xs text-gray-400">Computing...</p>}
      {error && <p className="text-xs text-red-500">{error}</p>}
      {result && result.n_filtered === 0 && (
        <p className="text-xs text-amber-600">
          No trials match the current constraints. Try relaxing your filters.
        </p>
      )}

      {/* Recommendation card */}
      {rec && result && result.n_filtered > 0 && (
        <div className="border-2 border-indigo-300 rounded-lg p-3 bg-indigo-50">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-bold text-indigo-700">★ Recommended Trial #{rec.number}</span>
            <span className="text-xs bg-indigo-200 text-indigo-800 px-1.5 py-0.5 rounded">
              Score: {result.score.toFixed(3)}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <span className="text-gray-500">Reward:</span>
            <span>{rec.reward_id}</span>
            {keys.map((k) => (
              <span key={k} className="text-gray-500">
                {OBJ_DISPLAY[k] || k}:
              </span>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs mt-1">
            {keys.map((k, i) => {
              const raw = rec.values[i] ?? 0;
              return (
                <span key={`v-${k}`} className="font-mono">
                  {typeof raw === "number" ? raw.toFixed(2) : raw}
                </span>
              );
            })}
          </div>
          <div className="mt-2 pt-2 border-t border-indigo-200">
            <p className="text-xs text-gray-500 mb-1">Hyperparameters:</p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs">
              {Object.entries(rec.params)
                .filter(([k]) => k !== "reward_id")
                .slice(0, 6)
                .map(([k, v]) => (
                  <span key={k} className="truncate">
                    <code className="font-semibold">{k}</code>:{" "}
                    {typeof v === "number" ? v.toExponential(3) : String(v)}
                  </span>
                ))}
            </div>
          </div>
          {keys.includes("convergence_steps") && (
            <p className="text-xs text-gray-400 mt-2">
              * Trials that never reached baseline show total_steps as convergence value.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
