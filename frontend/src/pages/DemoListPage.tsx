import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, type DemoInfo } from "../api/client";

export function DemoListPage() {
  const [demos, setDemos] = useState<DemoInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const navigate = useNavigate();

  const reload = () => {
    setLoading(true);
    api
      .listDemos()
      .then(setDemos)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(reload, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this demo? This cannot be undone.")) return;
    setDeleting(id);
    try {
      await api.deleteDemo(id);
      setDemos((prev) => prev.filter((d) => d.id !== id));
    } catch (e) {
      alert(String(e));
    } finally {
      setDeleting(null);
    }
  };

  if (loading) {
    return <div className="text-center text-gray-400 py-12">Loading...</div>;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-2">Failed to load demos.</p>
        <button onClick={reload} className="text-indigo-600 underline text-sm">
          Retry
        </button>
      </div>
    );
  }

  if (demos.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-400 text-lg mb-4">No demos collected yet.</p>
        <p className="text-gray-400 text-sm mb-6">
          Complete a PPO training run, then collect a demo from its detail page.
        </p>
        <Link
          to="/"
          className="bg-indigo-600 text-white px-5 py-2 rounded font-medium hover:bg-indigo-700"
        >
          Back to Experiments
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">
          Expert Demos ({demos.length})
        </h2>
      </div>

      <div className="grid gap-3">
        {demos.map((demo) => (
          <div
            key={demo.id}
            className="border rounded-lg p-4 bg-white hover:shadow-sm transition"
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium text-sm">{demo.name}</div>
                <div className="text-xs text-gray-500 mt-1 space-x-3">
                  <span>{demo.env_id}</span>
                  <span>{demo.n_episodes} episodes</span>
                  <span>{demo.n_steps.toLocaleString()} steps</span>
                  <span>{new Date(demo.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() =>
                    navigate(
                      `/new?demo_id=${demo.id}&env_id=${demo.env_id}&algo=BC`
                    )
                  }
                  className="px-3 py-1.5 text-xs font-medium bg-green-600 text-white rounded hover:bg-green-700"
                >
                  Clone (BC)
                </button>
                <button
                  onClick={() => handleDelete(demo.id)}
                  disabled={deleting === demo.id}
                  className="px-3 py-1.5 text-xs font-medium border border-red-200 text-red-600 rounded hover:bg-red-50 disabled:opacity-50"
                >
                  {deleting === demo.id ? "..." : "Delete"}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
