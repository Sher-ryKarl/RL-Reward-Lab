import type { EnvInfo } from "../../api/client";

interface Props {
  envs: EnvInfo[];
  selected: string;
  onChange: (id: string) => void;
}

export function EnvSelector({ envs, selected, onChange }: Props) {
  return (
    <fieldset className="border rounded p-4">
      <legend className="text-sm font-semibold text-gray-700">Environment</legend>
      <div className="flex gap-4 mt-2">
        {envs.map((e) => (
          <label key={e.env_id} className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="env"
              value={e.env_id}
              checked={selected === e.env_id}
              onChange={() => onChange(e.env_id)}
              className="accent-indigo-600"
            />
            <span>
              <span className="font-medium">{e.name}</span>
              <span className="text-xs text-gray-500 ml-1">({e.action_space})</span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
