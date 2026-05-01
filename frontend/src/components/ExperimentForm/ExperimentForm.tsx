import { useState } from "react";
import { api, type EnvInfo, type RewardInfo, type ExperimentCreate } from "../../api/client";
import { EnvSelector } from "./EnvSelector";
import { RewardMultiSelect } from "./RewardMultiSelect";
import { HyperParamPanel } from "./HyperParamPanel";

interface Props {
  envs: EnvInfo[];
  rewards: RewardInfo[];
}

export function ExperimentForm({ envs, rewards }: Props) {
  const [envId, setEnvId] = useState("MountainCar-v0");
  const [rewardIds, setRewardIds] = useState<string[]>(["R0_sparse", "R1_dense"]);
  const [hp, setHp] = useState({
    learning_rate: 3e-4,
    n_steps: 2048,
    batch_size: 64,
    gamma: 0.99,
    gae_lambda: 0.95,
    ent_coef: 0.0,
    clip_range: 0.2,
  });
  const [totalSteps, setTotalSteps] = useState(50_000);
  const [seeds, setSeeds] = useState([0]);
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState(false);

  const submit = async () => {
    if (rewardIds.length === 0) {
      setError("Select at least one reward variant.");
      return;
    }
    setSubmitting(true);
    setError(null);
    const body: ExperimentCreate = {
      name: name || `Exp-${Date.now().toString(36)}`,
      env_id: envId,
      algo_id: "PPO",
      reward_ids: rewardIds,
      hyperparams: hp,
      total_steps: totalSteps,
      seeds,
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
      <RewardMultiSelect rewards={rewards} selected={rewardIds} onChange={setRewardIds} />
      <HyperParamPanel hp={hp} onChange={setHp} />

      <div className="flex items-center gap-6">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-semibold text-gray-700">Total Steps</span>
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
    </div>
  );
}
