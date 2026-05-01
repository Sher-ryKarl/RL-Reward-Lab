interface Props {
  hp: Record<string, unknown>;
  onChange: (hp: Record<string, unknown>) => void;
  algoId: string;
}

export function HyperParamPanel({ hp, onChange, algoId }: Props) {
  const keys = Object.keys(hp).filter(
    (k) => typeof hp[k] === "number" || typeof hp[k] === "string"
  );

  const set = (key: string, val: string) => {
    const num = parseFloat(val);
    onChange({ ...hp, [key]: isNaN(num) ? val : num });
  };

  return (
    <fieldset className="border rounded p-4">
      <legend className="text-sm font-semibold text-gray-700">
        {algoId} Hyperparameters
      </legend>
      {keys.length === 0 ? (
        <p className="text-xs text-gray-400 mt-2">No hyperparameters to configure.</p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
          {keys.map((key) => {
            const val = hp[key];
            const isStr = typeof val === "string";
            return (
              <label key={key} className="flex flex-col gap-1">
                <span className="text-xs text-gray-500">{key}</span>
                <input
                  type={isStr ? "text" : "number"}
                  value={String(val)}
                  step={isStr ? undefined : "any"}
                  onChange={(e) => set(key, e.target.value)}
                  className="border rounded px-2 py-1 text-sm font-mono"
                />
              </label>
            );
          })}
        </div>
      )}
    </fieldset>
  );
}
