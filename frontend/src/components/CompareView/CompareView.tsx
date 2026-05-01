import { useState } from "react";
import { useExperimentStore } from "../../stores/experimentStore";

export function CompareView() {
  const { experiments } = useExperimentStore();
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggle = (id: string) => {
    const nxt = new Set(selected);
    if (nxt.has(id)) nxt.delete(id);
    else nxt.add(id);
    setSelected(nxt);
  };

  // Gather stream data for selected runs — simplified: show experiment names
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-800">Compare Experiments</h2>
      <p className="text-sm text-gray-500">
        Select experiments to compare. Full multi-run comparison will be available
        once training data is loaded.
      </p>

      {experiments.length === 0 ? (
        <div className="text-center text-gray-400 py-12">
          No experiments yet. Create one first.
        </div>
      ) : (
        <div className="grid gap-2">
          {experiments.map((exp) => (
            <label
              key={exp.id}
              className="flex items-center gap-3 p-3 border rounded cursor-pointer hover:bg-gray-50"
            >
              <input
                type="checkbox"
                checked={selected.has(exp.id)}
                onChange={() => toggle(exp.id)}
                className="accent-indigo-600"
              />
              <div>
                <div className="font-medium text-sm">{exp.name}</div>
                <div className="text-xs text-gray-500">
                  {exp.env_id} · {exp.algo_id} · {exp.runs.length} runs · {exp.status}
                </div>
              </div>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
