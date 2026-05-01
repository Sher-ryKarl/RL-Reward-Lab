import type { PPOHyper } from "../../api/client";

interface Props {
  hp: PPOHyper;
  onChange: (hp: PPOHyper) => void;
}

const defaults: PPOHyper = {
  learning_rate: 3e-4,
  n_steps: 2048,
  batch_size: 64,
  gamma: 0.99,
  gae_lambda: 0.95,
  ent_coef: 0.0,
  clip_range: 0.2,
};

export function HyperParamPanel({ hp, onChange }: Props) {
  const set = (key: keyof PPOHyper, val: string) => {
    onChange({ ...hp, [key]: parseFloat(val) || (defaults[key] as number) });
  };

  const fields: { key: keyof PPOHyper; label: string; step?: string }[] = [
    { key: "learning_rate", label: "Learning Rate", step: "0.0001" },
    { key: "n_steps", label: "n_steps" },
    { key: "batch_size", label: "Batch Size" },
    { key: "gamma", label: "Gamma", step: "0.01" },
    { key: "gae_lambda", label: "GAE Lambda", step: "0.01" },
    { key: "ent_coef", label: "Entropy Coef", step: "0.001" },
    { key: "clip_range", label: "Clip Range", step: "0.05" },
  ];

  return (
    <fieldset className="border rounded p-4">
      <legend className="text-sm font-semibold text-gray-700">
        PPO Hyperparameters
      </legend>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
        {fields.map(({ key, label, step }) => (
          <label key={key} className="flex flex-col gap-1">
            <span className="text-xs text-gray-500">{label}</span>
            <input
              type="number"
              value={hp[key]}
              step={step || "1"}
              onChange={(e) => set(key, e.target.value)}
              className="border rounded px-2 py-1 text-sm font-mono"
            />
          </label>
        ))}
      </div>
    </fieldset>
  );
}
