import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";

export function Navbar() {
  const loc = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const linkCls = (path: string) =>
    `px-3 py-2 rounded text-sm font-medium ${
      loc.pathname === path
        ? "bg-indigo-700 text-white"
        : "text-indigo-100 hover:bg-indigo-500"
    }`;

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <nav className="bg-indigo-600 shadow">
      <div className="max-w-7xl mx-auto px-4 flex items-center h-14 gap-1">
        <Link to="/" className="text-white font-bold text-lg mr-6">
          RL-Reward-Lab
        </Link>
        <Link to="/" className={linkCls("/")}>
          Experiments
        </Link>
        <Link to="/demos" className={linkCls("/demos")}>
          Demos
        </Link>
        <Link to="/new" className={linkCls("/new")}>
          New
        </Link>
        <Link to="/compare" className={linkCls("/compare")}>
          Compare
        </Link>
        <div className="flex-1" />
        {user && (
          <>
            <span className="text-indigo-200 text-sm">{user.username}</span>
            <button
              onClick={handleLogout}
              className="px-2 py-1 text-xs text-indigo-200 hover:text-white hover:bg-indigo-500 rounded"
            >
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
