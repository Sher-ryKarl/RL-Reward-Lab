import { useState } from "react";
import Editor from "@monaco-editor/react";
import { api, type RewardInfo } from "../../api/client";

const PLACEHOLDER = `def reward_fn(obs, reward, terminated, truncated):
    # obs: numpy array of environment observations
    # reward: original environment reward
    # terminated: True if episode ended (goal reached or failure)
    # truncated: True if episode was cut off by time limit
    return reward + float(obs[0])`;

interface Props {
  editing: RewardInfo | null;
  onClose: () => void;
  onCreated: (reward: RewardInfo) => void;
}

export function RewardEditor({ editing, onClose, onCreated }: Props) {
  const isPreset = editing && editing.source_type !== "custom";
  const [code, setCode] = useState(editing?.code || PLACEHOLDER);
  const [name, setName] = useState(
    isPreset ? `${editing?.name} (copy)` : editing?.name || ""
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setError(null);
    setSaving(true);
    try {
      const result = await api.createCustomReward({ name: name || "Custom", code });
      onCreated({
        id: result.reward_id,
        name: result.name,
        description: `Custom reward: ${result.name}`,
        source_type: "custom",
        terms: ["extrinsic"],
        references: [],
        code: result.code,
      });
      onClose();
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-3 border-b">
          <h3 className="font-semibold text-gray-800">
            {isPreset ? "Edit Preset Reward" : "Custom Reward Function"}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>

        <div className="p-4 space-y-3 flex-1 overflow-auto">
          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-gray-600">Name</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Reward"
              className="border rounded px-2 py-1 text-sm"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-gray-600">
              Python Code — <code className="bg-gray-100 px-1 rounded">def reward_fn(obs, reward, terminated, truncated) -&gt; float</code>
            </span>
            <div className="border rounded overflow-hidden" style={{ height: 300 }}>
              <Editor
                language="python"
                value={code}
                onChange={(v) => setCode(v || "")}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  fontSize: 13,
                  lineNumbers: "on",
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                }}
              />
            </div>
          </label>

          {isPreset && (
            <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded p-2">
              Editing a built-in preset creates a copy as a custom reward. The original preset is unchanged.
            </p>
          )}

          {error && (
            <div className="bg-red-50 border border-red-300 rounded p-2 text-sm text-red-700">
              {error}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 px-5 py-3 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-sm border rounded hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            onClick={save}
            disabled={saving}
            className="px-4 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save & Use"}
          </button>
        </div>
      </div>
    </div>
  );
}
