import { create } from "zustand";
import type { ExperimentSummary } from "../api/client";

interface ExperimentStore {
  experiments: ExperimentSummary[];
  selectedId: string | null;
  setExperiments: (items: ExperimentSummary[]) => void;
  setSelected: (id: string | null) => void;
  updateRunStatus: (
    experimentId: string,
    runId: string,
    status: string,
  ) => void;
}

export const useExperimentStore = create<ExperimentStore>((set) => ({
  experiments: [],
  selectedId: null,

  setExperiments: (items) => set({ experiments: items }),

  setSelected: (id) => set({ selectedId: id }),

  updateRunStatus: (experimentId, runId, status) =>
    set((state) => ({
      experiments: state.experiments.map((exp) =>
        exp.id === experimentId
          ? {
              ...exp,
              runs: exp.runs.map((r) =>
                r.id === runId ? { ...r, status } : r,
              ),
              status: exp.runs.every((r) =>
                r.id === runId ? status !== "running" : r.status !== "running",
              )
                ? "done"
                : exp.status,
            }
          : exp,
      ),
    })),
}));
