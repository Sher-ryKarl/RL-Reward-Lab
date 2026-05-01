import { useEffect, useState } from "react";
import { api } from "../../api/client";

interface Props {
  runId: string;
  runStatus?: string;
}

export function ReplayViewer({ runId, runStatus }: Props) {
  const [videoError, setVideoError] = useState(false);
  const videoUrl = api.replayUrl(runId);

  // Reset error state when runId changes
  useEffect(() => {
    setVideoError(false);
  }, [runId]);

  if (runStatus && runStatus !== "done") {
    return (
      <div className="border rounded p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Replay</h3>
        <p className="text-sm text-gray-400">
          Replay video will be available after training completes.
        </p>
      </div>
    );
  }

  return (
    <div className="border rounded p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Replay</h3>
      {videoError ? (
        <p className="text-sm text-gray-400">
          No replay video available for this run.
        </p>
      ) : (
        <video
          key={runId}
          controls
          className="w-full max-h-96 rounded bg-black"
          onError={() => setVideoError(true)}
          onLoadedData={() => setVideoError(false)}
        >
          <source src={videoUrl} type="video/mp4" />
        </video>
      )}
    </div>
  );
}
