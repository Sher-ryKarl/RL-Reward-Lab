import { useEffect, useState } from "react";
import { api, type AlgoInfo, type DemoInfo, type EnvInfo, type RewardInfo, type ExperimentCreate } from "../../api/client";
import { EnvSelector } from "./EnvSelector";
import { RewardMultiSelect } from "./RewardMultiSelect";
import { HyperParamPanel } from "./HyperParamPanel";
import { SearchSpaceEditor } from "./SearchSpaceEditor";
import { RewardEditor } from "./RewardEditor";

interface Props {
  envs: EnvInfo[];
  algos: AlgoInfo[];
  rewards: RewardInfo[];
}

export function ExperimentForm({ envs, algos, rewards: initialRewards }: Props) {
  const [envId, setEnvId] = useState("MountainCar-v0");
  const [algoId, setAlgoId] = useState("PPO");
  const [rewardIds, setRewardIds] = useState<string[]>(["R0_sparse", "R1_dense"]);
  const [hp, setHp] = useState<Record<string, unknown>>({});
  const [totalSteps, setTotalSteps] = useState(50_000);
  const [seeds, setSeeds] = useState([0]);
  const [name, setName] = useState("");
  const [optimize, setOptimize] = useState(false);
  const [searchSpace, setSearchSpace] = useState<Record<string, Record<string, unknown>>>({});
  const [nTrials, setNTrials] = useState(30);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState(false);
  const [demos, setDemos] = useState<DemoInfo[]>([]);
  const [demoId, setDemoId] = useState<string | null>(null);
  const [rewards, setRewards] = useState<RewardInfo[]>(initialRewards);
  const [editingReward, setEditingReward] = useState<RewardInfo | null | undefined>(undefined);

  // Reset hyperparams when algo changes
  useEffect(() => {
    const algo = algos.find((a) => a.algo_id === algoId);
    if (algo) setHp({ ...algo.default_hp });
  }, [algoId, algos]);

  // Fetch demos when envId changes (for BC demo selector)
  useEffect(() => {
    api.listDemos().then(setDemos).catch(() => setDemos([]));
  }, [envId]);

  // Refresh rewards list to include any custom ones
  useEffect(() => {
    api.listRewards().then(setRewards).catch(() => {});
  }, []);

  const selectedAlgo = algos.find((a) => a.algo_id === algoId);
  const isBC = algoId === "BC";
  const filteredDemos = demos.filter((d) => d.env_id === envId);

  const handleRewardCreated = (reward: RewardInfo) => {
    setRewards((prev) => [...prev, reward]);
    setRewardIds((prev) => [...prev, reward.id]);
  };

  const submit = async () => {
    if (rewardIds.length === 0) {
      setError("Select at least one reward variant.");
      return;
    }
    if (optimize && Object.keys(searchSpace).length === 0) {
      setError("Optimization requires at least one search space dimension.");
      return;
    }
    if (isBC && !demoId) {
      setError("BC requires a demo to clone from. Collect one first or select an existing demo.");
      return;
    }
    setSubmitting(true);
    setError(null);
    const body: ExperimentCreate = {
      name: name || `Exp-${Date.now().toString(36)}`,
      env_id: envId,
      algo_id: algoId as ExperimentCreate["algo_id"],
      reward_ids: rewardIds,
      hyperparams: hp,
      total_steps: totalSteps,
      seeds,
      optimize,
      search_space: searchSpace,
      n_trials: nTrials,
      demo_id: isBC ? demoId : null,
    };
    try {
      await api.createExperiment(body);
      setCreated(true);
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  };

  if (created) {
    return (
      <div className="bg-green-50 border border-green-300 rounded p-6 text-center">
        <p className="text-green-800 text-lg font-semibold">Experiment submitted!</p>
        <p className="text-green-600 mt-2">
          Training has started. Go to the Experiments page to monitor progress.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="text-sm font-semibold text-gray-700">
          Experiment Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Optional — auto-generated if blank"
          className="w-full border rounded px-3 py-2 mt-1 text-sm"
        />
      </div>

      <EnvSelector envs={envs} selected={envId} onChange={setEnvId} />

      {/* ── Algorithm Selector (v0.4) ──────────────────────────────── */}
      <fieldset className="border rounded p-4">
        <legend className="text-sm font-semibold text-gray-700">Algorithm</legend>
        <div className="flex gap-4 mt-2">
          {algos.map((a) => {
            const canUse = envs.find((e) => e.env_id === envId);
            const supported = canUse
              ? (canUse.action_space === "discrete" && a.discrete) ||
                (canUse.action_space === "continuous" && a.continuous)
              : false;
            return (
              <label
                key={a.algo_id}
                className={`flex items-center gap-2 ${
                  supported ? "cursor-pointer" : "opacity-40 cursor-not-allowed"
                }`}
              >
                <input
                  type="radio"
                  name="algo"
                  value={a.algo_id}
                  checked={selectedAlgo?.algo_id === a.algo_id}
                  disabled={!supported}
                  onChange={() => supported && setAlgoId(a.algo_id)}
                  className="accent-indigo-600"
                />
                <span className="font-medium">{a.name}</span>
                <span className="text-xs text-gray-400">({a.algo_id})</span>
              </label>
            );
          })}
        </div>
      </fieldset>

      {/* ── Demo Selector (BC only, v0.5) ─────────────────────────── */}
      {isBC && (
        <fieldset className="border rounded p-4 bg-indigo-50">
          <legend className="text-sm font-semibold text-indigo-700">
            Clone Source (Expert Demo)
          </legend>
          {filteredDemos.length === 0 ? (
            <p className="text-xs text-gray-500 mt-2">
              No demos available for {envId}. Run a PPO experiment first, then collect a demo from it.
            </p>
          ) : (
            <select
              value={demoId ?? ""}
              onChange={(e) => setDemoId(e.target.value || null)}
              className="border rounded px-2 py-1 text-sm mt-2 w-full"
            >
              <option value="">-- Select a demo --</option>
              {filteredDemos.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.n_episodes} eps, {d.n_steps} steps)
                </option>
              ))}
            </select>
          )}
        </fieldset>
      )}

      <RewardMultiSelect
        rewards={rewards}
        selected={rewardIds}
        onChange={setRewardIds}
        onEdit={(r) => setEditingReward(r)}
      />
      <HyperParamPanel hp={hp} onChange={setHp} algoId={algoId} />

      {/* ── Optimization Toggle (v0.2, not for BC) ──────────────────── */}
      {!isBC && (
      <div className="border rounded p-3 space-y-3 bg-gray-50">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={optimize}
            onChange={(e) => setOptimize(e.target.checked)}
            className="w-4 h-4"
          />
          <span className="text-sm font-semibold text-gray-700">
            Optuna Hyperparameter Optimization
          </span>
        </label>

        {optimize && (
          <>
            <SearchSpaceEditor value={searchSpace} onChange={setSearchSpace} />
            <label className="flex flex-col gap-1">
              <span className="text-xs font-semibold text-gray-700">Number of Trials</span>
              <input
                type="number"
                value={nTrials}
                onChange={(e) => setNTrials(Number(e.target.value))}
                min={2}
                max={500}
                className="border rounded px-2 py-1 text-sm font-mono w-24"
              />
            </label>
            <p className="text-xs text-gray-500">
              Optuna will search the hyperparameter space using TPE sampler. Each trial trains a
              PPO agent. Baseline hyperparameters above are used as fixed values for parameters
              not included in the search.
            </p>
          </>
        )}
      </div>
      )}

      <div className="flex items-center gap-6">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-semibold text-gray-700">
            {isBC ? "Training Batches" : "Total Steps"}
          </span>
          <input
            type="number"
            value={totalSteps}
            onChange={(e) => setTotalSteps(Number(e.target.value))}
            min={1000}
            max={2_000_000}
            step={5000}
            className="border rounded px-2 py-1 text-sm font-mono w-28"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-semibold text-gray-700">Seeds (comma)</span>
          <input
            type="text"
            value={seeds.join(",")}
            onChange={(e) =>
              setSeeds(e.target.value.split(",").map(Number).filter((n) => !isNaN(n)))
            }
            className="border rounded px-2 py-1 text-sm font-mono w-28"
          />
        </label>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-300 rounded p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <button
        onClick={submit}
        disabled={submitting}
        className="bg-indigo-600 text-white px-6 py-2.5 rounded font-medium hover:bg-indigo-700 disabled:opacity-50"
      >
        {submitting ? "Submitting..." : "Start Experiment"}
      </button>

      {editingReward !== undefined && (
        <RewardEditor
          editing={editingReward}
          onClose={() => setEditingReward(undefined)}
          onCreated={handleRewardCreated}
        />
      )}
    </div>
  );
}
