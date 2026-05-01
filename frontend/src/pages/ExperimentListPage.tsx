import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, type ExperimentSummary } from "../api/client";

const STATUSES = ["", "pending", "running", "done", "failed", "cancelled"];
const PAGE_SIZES = [10, 20, 50];

export function ExperimentListPage() {
  const [exps, setExps] = useState<ExperimentSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterStatus, setFilterStatus] = useState("");
  const [filterEnv, setFilterEnv] = useState("");
  const [filterAlgo, setFilterAlgo] = useState("");
  const [search, setSearch] = useState("");

  // Selection
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  const reload = async () => {
    setLoading(true);
    try {
      const data = await api.listExperiments({
        page,
        size,
        status: filterStatus || undefined,
        env_id: filterEnv || undefined,
        algo_id: filterAlgo || undefined,
        search: search || undefined,
      });
      setExps(data.items);
      setTotal(data.total);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    reload();
    const interval = setInterval(reload, 5_000);
    return () => clearInterval(interval);
  }, [page, size, filterStatus, filterEnv, filterAlgo, search]);

  const totalPages = Math.max(1, Math.ceil(total / size));

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === exps.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(exps.map((e) => e.id)));
    }
  };

  const compareSelected = () => {
    if (selected.size < 2) return;
    const ids = Array.from(selected);
    navigate(`/compare?ids=${ids.join(",")}`);
  };

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      pending: "bg-gray-100 text-gray-600",
      running: "bg-blue-100 text-blue-700",
      done: "bg-green-100 text-green-700",
      failed: "bg-red-100 text-red-700",
      cancelled: "bg-yellow-100 text-yellow-700",
    };
    return `px-2 py-0.5 rounded-full text-xs font-medium ${map[status] || map.pending}`;
  };

  if (loading && exps.length === 0) {
    return <div className="text-center text-gray-400 py-12">Loading...</div>;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-2">Failed to load experiments.</p>
        <button onClick={reload} className="text-indigo-600 underline text-sm">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">
          Experiments
          {total > 0 && (
            <span className="text-sm font-normal text-gray-400 ml-2">
              ({total} total)
            </span>
          )}
        </h2>
        <div className="flex items-center gap-2">
          {selected.size >= 2 && (
            <button
              onClick={compareSelected}
              className="bg-green-600 text-white px-3 py-2 rounded text-sm font-medium hover:bg-green-700"
            >
              Compare ({selected.size})
            </button>
          )}
          <Link
            to="/new"
            className="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-indigo-700"
          >
            + New
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="Search name..."
          className="border rounded px-3 py-1.5 text-sm w-48"
        />
        <select
          value={filterStatus}
          onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
          className="border rounded px-2 py-1.5 text-sm"
        >
          <option value="">All status</option>
          {STATUSES.filter(Boolean).map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <input
          type="text"
          value={filterEnv}
          onChange={(e) => { setFilterEnv(e.target.value); setPage(1); }}
          placeholder="Env ID"
          className="border rounded px-2 py-1.5 text-sm w-36"
        />
        <input
          type="text"
          value={filterAlgo}
          onChange={(e) => { setFilterAlgo(e.target.value); setPage(1); }}
          placeholder="Algo ID"
          className="border rounded px-2 py-1.5 text-sm w-24"
        />
        {(filterStatus || filterEnv || filterAlgo || search) && (
          <button
            onClick={() => {
              setFilterStatus("");
              setFilterEnv("");
              setFilterAlgo("");
              setSearch("");
              setPage(1);
            }}
            className="text-xs text-gray-500 hover:text-gray-700 ml-1"
          >
            Clear filters
          </button>
        )}
      </div>

      {exps.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-400 text-lg mb-4">No experiments found.</p>
          <Link
            to="/new"
            className="bg-indigo-600 text-white px-5 py-2 rounded font-medium hover:bg-indigo-700"
          >
            Create First Experiment
          </Link>
        </div>
      ) : (
        <>
          {/* Select all */}
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={selected.size === exps.length && exps.length > 0}
              onChange={toggleAll}
              className="accent-indigo-600"
            />
            Select all on page
          </label>

          {/* Experiment cards */}
          <div className="grid gap-3">
            {exps.map((exp) => (
              <div
                key={exp.id}
                className="border rounded-lg bg-white hover:shadow-sm transition flex items-start gap-3 p-4"
              >
                <input
                  type="checkbox"
                  checked={selected.has(exp.id)}
                  onChange={() => toggleSelect(exp.id)}
                  className="mt-0.5 accent-indigo-600"
                />
                <Link
                  to={`/experiments/${exp.id}`}
                  className="flex-1 min-w-0"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{exp.name}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {exp.env_id} · {exp.algo_id} · {exp.total_steps.toLocaleString()} steps
                        · {new Date(exp.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={statusBadge(exp.status)}>{exp.status}</span>
                      <span className="text-xs text-gray-400">{exp.runs.length} run{exp.runs.length !== 1 ? "s" : ""}</span>
                    </div>
                  </div>
                </Link>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500">Rows:</span>
                {PAGE_SIZES.map((s) => (
                  <button
                    key={s}
                    onClick={() => { setSize(s); setPage(1); }}
                    className={`px-2 py-0.5 rounded ${
                      size === s
                        ? "bg-indigo-100 text-indigo-700 font-medium"
                        : "text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1 text-sm">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 rounded border disabled:opacity-30 hover:bg-gray-100"
                >
                  Prev
                </button>
                <span className="px-3 py-1 text-gray-600">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 rounded border disabled:opacity-30 hover:bg-gray-100"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
