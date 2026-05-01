import { useState } from "react";

const PPO_PARAMS = [
  "learning_rate",
  "n_steps",
  "batch_size",
  "gamma",
  "gae_lambda",
  "ent_coef",
  "clip_range",
] as const;

const DIST_TYPES: { value: string; label: string; fields: string[] }[] = [
  { value: "loguniform", label: "Log Uniform", fields: ["low", "high"] },
  { value: "uniform", label: "Uniform", fields: ["low", "high"] },
  { value: "int", label: "Integer", fields: ["low", "high"] },
  { value: "categorical", label: "Categorical", fields: ["choices"] },
  { value: "discrete_uniform", label: "Discrete Uniform", fields: ["low", "high", "q"] },
];

interface SearchEntry {
  name: string;
  type: string;
  low?: number;
  high?: number;
  choices?: string;
  q?: number;
}

interface Props {
  value: Record<string, Record<string, unknown>>;
  onChange: (v: Record<string, Record<string, unknown>>) => void;
}

export function SearchSpaceEditor({ value, onChange }: Props) {
  const [entries, setEntries] = useState<SearchEntry[]>(() => entriesFromValue(value));

  function entriesFromValue(
    v: Record<string, Record<string, unknown>>,
  ): SearchEntry[] {
    return Object.entries(v).map(([name, spec]) => ({
      name,
      type: (spec.type as string) || "loguniform",
      low: spec.low as number | undefined,
      high: spec.high as number | undefined,
      choices: spec.choices ? (spec.choices as string[]).join(",") : undefined,
      q: spec.q as number | undefined,
    }));
  }

  function sync(updated: SearchEntry[]) {
    setEntries(updated);
    const obj: Record<string, Record<string, unknown>> = {};
    for (const e of updated) {
      const spec: Record<string, unknown> = { type: e.type };
      if (e.low !== undefined) spec.low = e.low;
      if (e.high !== undefined) spec.high = e.high;
      if (e.type === "categorical" && e.choices) {
        spec.choices = e.choices.split(",").map((s) => s.trim());
      }
      if (e.type === "discrete_uniform" && e.q !== undefined) spec.q = e.q;
      obj[e.name] = spec;
    }
    onChange(obj);
  }

  function add() {
    const used = new Set(entries.map((e) => e.name));
    const next = PPO_PARAMS.find((p) => !used.has(p)) || PPO_PARAMS[0];
    sync([...entries, { name: next, type: "loguniform", low: 1e-6, high: 1.0 }]);
  }

  function remove(i: number) {
    sync(entries.filter((_, idx) => idx !== i));
  }

  function update(i: number, patch: Partial<SearchEntry>) {
    sync(entries.map((e, idx) => (idx === i ? { ...e, ...patch } : e)));
  }

  const distFields = (type: string) =>
    DIST_TYPES.find((d) => d.value === type)?.fields || [];

  return (
    <div className="border rounded p-3 space-y-2 bg-gray-50">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-700">
          Hyperparameter Search Space
        </span>
        <button
          type="button"
          onClick={add}
          disabled={entries.length >= PPO_PARAMS.length}
          className="text-xs bg-white border rounded px-2 py-1 hover:bg-gray-100 disabled:opacity-40"
        >
          + Add Param
        </button>
      </div>

      {entries.length === 0 && (
        <p className="text-xs text-gray-500 italic">
          No search dimensions. Click "Add Param" to define ranges for hyperparameter optimization.
        </p>
      )}

      {entries.map((entry, i) => {
        const fields = distFields(entry.type);
        const used = new Set(entries.map((e) => e.name));
        return (
          <div
            key={i}
            className="flex items-center gap-2 bg-white rounded border p-2 text-xs flex-wrap"
          >
            <select
              value={entry.name}
              onChange={(e) => update(i, { name: e.target.value })}
              className="border rounded px-1 py-1"
            >
              {PPO_PARAMS.map((p) => (
                <option key={p} value={p} disabled={used.has(p) && p !== entry.name}>
                  {p}
                </option>
              ))}
            </select>

            <select
              value={entry.type}
              onChange={(e) => {
                const newType = e.target.value;
                const patch: Partial<SearchEntry> = { type: newType };
                if (newType === "int") {
                  patch.low = entry.low ? Math.round(entry.low) : 1;
                  patch.high = entry.high ? Math.round(entry.high) : 100;
                }
                update(i, patch);
              }}
              className="border rounded px-1 py-1"
            >
              {DIST_TYPES.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>

            {fields.includes("low") && (
              <input
                type="number"
                value={entry.low ?? ""}
                onChange={(e) => update(i, { low: Number(e.target.value) })}
                placeholder="low"
                className="border rounded px-1 py-1 w-20"
                step={entry.type === "int" ? 1 : "any"}
              />
            )}

            {fields.includes("high") && (
              <input
                type="number"
                value={entry.high ?? ""}
                onChange={(e) => update(i, { high: Number(e.target.value) })}
                placeholder="high"
                className="border rounded px-1 py-1 w-20"
                step={entry.type === "int" ? 1 : "any"}
              />
            )}

            {fields.includes("choices") && (
              <input
                type="text"
                value={entry.choices || ""}
                onChange={(e) => update(i, { choices: e.target.value })}
                placeholder="a,b,c"
                className="border rounded px-1 py-1 w-32"
              />
            )}

            {fields.includes("q") && (
              <input
                type="number"
                value={entry.q ?? ""}
                onChange={(e) => update(i, { q: Number(e.target.value) })}
                placeholder="step"
                className="border rounded px-1 py-1 w-16"
                step="any"
              />
            )}

            <button
              type="button"
              onClick={() => remove(i)}
              className="text-red-500 hover:text-red-700 ml-auto"
            >
              ✕
            </button>
          </div>
        );
      })}
    </div>
  );
}
