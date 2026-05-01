interface Props {
  runId: string;
}

export function ReplayViewer({ runId }: Props) {
  // In v0.1, replay is a simple video served by MLflow artifact route.
  // Full path available in RunSummary.artifact_path after training finishes.
  return (
    <div className="border rounded p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">
        Replay — Run <code className="text-indigo-600">{runId}</code>
      </h3>
      <p className="text-sm text-gray-500">
        Replay video will be available after training completes.
      </p>
    </div>
  );
}
