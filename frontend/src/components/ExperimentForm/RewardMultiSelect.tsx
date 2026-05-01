import type { RewardInfo } from "../../api/client";

interface Props {
  rewards: RewardInfo[];
  selected: string[];
  onChange: (ids: string[]) => void;
  onEdit?: (reward: RewardInfo | null) => void;
}

export function RewardMultiSelect({ rewards, selected, onChange, onEdit }: Props) {
  const toggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  return (
    <fieldset className="border rounded p-4">
      <div className="flex items-center justify-between">
        <legend className="text-sm font-semibold text-gray-700">
          Reward Variants
        </legend>
        {onEdit && (
          <button
            type="button"
            onClick={() => onEdit(null)}
            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
          >
            + Custom Reward
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-3 mt-2">
        {rewards.map((r) => {
          const isMisleading = r.name.includes("⚠");
          const isCustom = r.source_type === "custom";
          return (
            <label
              key={r.id}
              className={`flex items-start gap-2 p-2 rounded border cursor-pointer ${
                selected.includes(r.id)
                  ? "border-indigo-500 bg-indigo-50"
                  : "border-gray-200 hover:border-gray-300"
              } ${isMisleading ? "border-red-300 bg-red-50" : ""}`}
            >
              <input
                type="checkbox"
                checked={selected.includes(r.id)}
                onChange={() => toggle(r.id)}
                className="mt-0.5 accent-indigo-600"
              />
              <div>
                <div className={`text-sm font-medium ${isMisleading ? "text-red-700" : ""}`}>
                  {r.name}
                  {isCustom && (
                    <span className="ml-1 text-xs text-indigo-500 font-normal">(custom)</span>
                  )}
                </div>
                <div className="text-xs text-gray-500 max-w-xs">{r.description}</div>
                {onEdit && (
                  <button
                    type="button"
                    onClick={(e) => { e.preventDefault(); onEdit(r); }}
                    className="text-xs text-indigo-500 hover:text-indigo-700 mt-0.5"
                  >
                    {isCustom ? "Edit" : "View Source"}
                  </button>
                )}
              </div>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
