import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, type AlgoInfo, type EnvInfo, type RewardInfo } from "../api/client";
import { ExperimentForm } from "../components/ExperimentForm/ExperimentForm";

export function NewExperimentPage() {
  const [envs, setEnvs] = useState<EnvInfo[]>([]);
  const [algos, setAlgos] = useState<AlgoInfo[]>([]);
  const [rewards, setRewards] = useState<RewardInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams] = useSearchParams();

  const prefill = useMemo(
    () => ({
      demo_id: searchParams.get("demo_id") || null,
      env_id: searchParams.get("env_id") || null,
      algo_id: searchParams.get("algo") || null,
    }),
    [searchParams]
  );

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
          Please check that the backend server is running and accessible.
        </p>
      </div>
    );
  }

  return (
    <div>
      <Link to="/" className="text-sm text-indigo-600 hover:underline">
        ← Back to Experiments
      </Link>
      <h2 className="text-lg font-semibold text-gray-800 mt-1 mb-4">New Experiment</h2>
      <ExperimentForm envs={envs} algos={algos} rewards={rewards} prefill={prefill} />
    </div>
  );
}
