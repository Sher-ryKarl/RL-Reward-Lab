/**
 * API client for RL-Reward-Lab backend.
 * Types are inferred from usage until openapi-typescript generation is wired.
 */

const TOKEN_KEY = "rl_lab_token";

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(url, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    window.location.href = `/login?from=${encodeURIComponent(window.location.pathname)}`;
    throw new Error("401: Authentication required");
  }
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
  code?: string;
}

export interface AlgoInfo {
  algo_id: string;
  name: string;
  discrete: boolean;
  continuous: boolean;
  default_hp: Record<string, unknown>;
}

export interface DemoInfo {
  id: string;
  name: string;
  env_id: string;
  reward_id: string | null;
  source_run_id: string | null;
  n_episodes: number;
  n_steps: number;
  created_at: string;
}

export interface ExperimentCreate {
  name: string;
  env_id: string;
  algo_id: "PPO" | "DQN" | "SAC" | "BC";
  reward_ids: string[];
  hyperparams: Record<string, unknown>;
  total_steps: number;
  seeds: number[];
  optimize?: boolean;
  search_space?: Record<string, Record<string, unknown>>;
  n_trials?: number;
  demo_id?: string | null;
}

export interface TrialResult {
  number: number;
  value: number;
  params: Record<string, unknown>;
  reward_id: string;
}

export interface PerRewardResult {
  best_value: number;
  best_params: Record<string, unknown>;
  n_trials: number;
  trials: TrialResult[];
}

export interface OptimizationResult {
  experiment_id: string;
  n_trials: number;
  best_value: number | null;
  best_params: Record<string, unknown>;
  trials: TrialResult[];
  status: string;
  per_reward: Record<string, PerRewardResult>;
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

  listExperiments: (params?: {
    page?: number;
    size?: number;
    status?: string;
    env_id?: string;
    algo_id?: string;
    search?: string;
  }) => {
    const qs = new URLSearchParams();
    if (params?.page) qs.set("page", String(params.page));
    if (params?.size) qs.set("size", String(params.size));
    if (params?.status) qs.set("status", params.status);
    if (params?.env_id) qs.set("env_id", params.env_id);
    if (params?.algo_id) qs.set("algo_id", params.algo_id);
    if (params?.search) qs.set("search", params.search);
    return request<ExperimentList>(`/api/v1/experiments?${qs.toString()}`);
  },

  getExperiment: (id: string) =>
    request<ExperimentSummary>(`/api/v1/experiments/${id}`),

  getOptimization: (id: string) =>
    request<OptimizationResult>(`/api/v1/experiments/${id}/optimization`),

  // Runs
  getRun: (id: string) => request<RunSummary>(`/api/v1/runs/${id}`),

  cancelRun: (id: string) =>
    request<{ status: string }>(`/api/v1/runs/${id}`, { method: "DELETE" }),

  // Custom Rewards (v0.6)
  createCustomReward: (body: { name: string; code: string }) =>
    request<{ reward_id: string; name: string; code: string }>(
      "/api/v1/rewards/custom",
      { method: "POST", body: JSON.stringify(body) }
    ),

  deleteCustomReward: (rewardId: string) =>
    request<void>(`/api/v1/rewards/custom/${rewardId}`, { method: "DELETE" }),

  // Demos (v0.5)
  listDemos: () => request<DemoInfo[]>("/api/v1/demos"),

  getDemo: (id: string) => request<DemoInfo>(`/api/v1/demos/${id}`),

  deleteDemo: (id: string) =>
    request<void>(`/api/v1/demos/${id}`, { method: "DELETE" }),

  createDemo: (body: {
    name: string;
    env_id: string;
    source_run_id: string;
    n_episodes: number;
    min_timesteps: number;
  }) =>
    request<DemoInfo>("/api/v1/demos", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // SSE stream — handled separately in stream.ts
  streamUrl: (runId: string) => `/api/v1/runs/${runId}/stream`,

  // Replay video
  replayUrl: (runId: string) => `/api/v1/runs/${runId}/replay`,
  replayStatus: (runId: string) =>
    request<{ available: boolean; reason: string }>(
      `/api/v1/runs/${runId}/replay/status`
    ),
};
