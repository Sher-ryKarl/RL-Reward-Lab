/**
 * API client for RL-Reward-Lab backend.
 * Types are inferred from usage until openapi-typescript generation is wired.
 */

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface EnvInfo {
  env_id: string;
  name: string;
  action_space: string;
}

export interface RewardInfo {
  id: string;
  name: string;
  description: string;
  source_type: string;
  terms: string[];
  references: string[];
}

export interface AlgoInfo {
  algo_id: string;
  name: string;
  discrete: boolean;
  continuous: boolean;
  default_hp: Record<string, unknown>;
}

export interface ExperimentCreate {
  name: string;
  env_id: string;
  algo_id: "PPO" | "DQN" | "SAC";
  reward_ids: string[];
  hyperparams: Record<string, unknown>;
  total_steps: number;
  seeds: number[];
  optimize?: boolean;
  search_space?: Record<string, Record<string, unknown>>;
  n_trials?: number;
}

export interface TrialResult {
  number: number;
  value: number;
  params: Record<string, unknown>;
}

export interface OptimizationResult {
  experiment_id: string;
  n_trials: number;
  best_value: number | null;
  best_params: Record<string, unknown>;
  trials: TrialResult[];
  status: string;
}

export interface RunSummary {
  id: string;
  reward_id: string;
  seed: number;
  status: string;
  hyperparams: Record<string, unknown>;
  final_metrics: Record<string, number>;
  started_at: string | null;
  ended_at: string | null;
}

export interface ExperimentSummary {
  id: string;
  name: string;
  env_id: string;
  algo_id: string;
  total_steps: number;
  status: string;
  created_at: string;
  runs: RunSummary[];
}

export interface ExperimentList {
  items: ExperimentSummary[];
  total: number;
  page: number;
  size: number;
}

export interface MetricEvent {
  run_id: string;
  reward_id: string;
  step: number;
  wall_time: number;
  metrics: Record<string, number>;
  components: Record<string, number> | null;
}

// ── API functions ────────────────────────────────────────────────────────────

export const api = {
  // Envs
  listEnvs: () => request<EnvInfo[]>("/api/v1/envs"),

  // Algos
  listAlgos: () => request<AlgoInfo[]>("/api/v1/algos"),

  // Rewards
  listRewards: () => request<RewardInfo[]>("/api/v1/rewards"),

  // Experiments
  createExperiment: (body: ExperimentCreate) =>
    request<ExperimentSummary>("/api/v1/experiments", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listExperiments: (page = 1, size = 20) =>
    request<ExperimentList>(`/api/v1/experiments?page=${page}&size=${size}`),

  getExperiment: (id: string) =>
    request<ExperimentSummary>(`/api/v1/experiments/${id}`),

  getOptimization: (id: string) =>
    request<OptimizationResult>(`/api/v1/experiments/${id}/optimization`),

  // Runs
  getRun: (id: string) => request<RunSummary>(`/api/v1/runs/${id}`),

  cancelRun: (id: string) =>
    request<{ status: string }>(`/api/v1/runs/${id}`, { method: "DELETE" }),

  // SSE stream — handled separately in stream.ts
  streamUrl: (runId: string) => `/api/v1/runs/${runId}/stream`,
};
