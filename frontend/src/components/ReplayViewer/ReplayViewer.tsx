import { useEffect, useState } from "react";
import { api } from "../../api/client";

interface Props {
  runId: string;
  runStatus?: string;
}

export function ReplayViewer({ runId, runStatus }: Props) {
  const [videoError, setVideoError] = useState(false);
  const [videoReason, setVideoReason] = useState<string | null>(null);
  const videoUrl = api.replayUrl(runId);

  useEffect(() => {
    setVideoError(false);
    setVideoReason(null);
  }, [runId]);

  useEffect(() => {
    if (runStatus === "done") {
      api.replayStatus(runId).then(
        (s) => {
          if (!s.available) setVideoReason(s.reason);
        },
        () => {},
      );
    }
  }, [runId, runStatus]);

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

  const reasonText: Record<string, string> = {
    encoding_failed:
      "Video recording failed (ffmpeg not available in the training environment).",
    not_recorded: "No replay video was recorded for this run.",
  };

  return (
    <div className="border rounded p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Replay</h3>
      {videoError || videoReason ? (
        <p className="text-sm text-gray-400">
          {reasonText[videoReason || ""] ||
            "No replay video available for this run."}
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
