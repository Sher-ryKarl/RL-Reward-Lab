import { useEffect, useState } from "react";
import { api, type AlgoInfo, type EnvInfo, type RewardInfo } from "../api/client";
import { ExperimentForm } from "../components/ExperimentForm/ExperimentForm";

export function NewExperimentPage() {
  const [envs, setEnvs] = useState<EnvInfo[]>([]);
  const [algos, setAlgos] = useState<AlgoInfo[]>([]);
  const [rewards, setRewards] = useState<RewardInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listEnvs(), api.listAlgos(), api.listRewards()])
      .then(([e, a, r]) => {
        setEnvs(e);
        setAlgos(a);
        setRewards(r);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-center text-gray-400 py-12">Loading...</div>;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Failed to load environments and rewards from backend.</p>
        <p className="text-sm text-gray-500 mt-2">
          Make sure the backend is running on http://localhost:8000
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-800 mb-4">New Experiment</h2>
      <ExperimentForm envs={envs} algos={algos} rewards={rewards} />
    </div>
  );
}
