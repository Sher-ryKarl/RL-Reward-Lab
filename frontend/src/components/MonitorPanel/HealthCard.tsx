interface Props {
  metrics: Record<string, number> | null;
}

const labelMap: Record<string, string> = {
  approx_kl: "Approx KL",
  entropy_loss: "Entropy Loss",
  value_loss: "Value Loss",
  explained_variance: "Explained Variance",
};

export function HealthCard({ metrics }: Props) {
  if (!metrics) {
    return (
      <div className="border rounded p-4 text-sm text-gray-400">
        Waiting for training data...
      </div>
    );
  }

  return (
    <div className="border rounded p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        PPO Training Health
      </h3>
      <div className="grid grid-cols-2 gap-3">
        {Object.entries(labelMap).map(([key, label]) => (
          <div key={key} className="bg-gray-50 rounded p-2">
            <div className="text-xs text-gray-500">{label}</div>
            <div className="text-lg font-mono font-medium">
              {key in metrics
                ? Number(metrics[key]).toFixed(4)
                : "—"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
