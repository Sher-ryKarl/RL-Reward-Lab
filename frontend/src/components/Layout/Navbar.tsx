import { Link, useLocation } from "react-router-dom";

export function Navbar() {
  const loc = useLocation();
  const linkCls = (path: string) =>
    `px-3 py-2 rounded text-sm font-medium ${
      loc.pathname === path
        ? "bg-indigo-700 text-white"
        : "text-indigo-100 hover:bg-indigo-500"
    }`;

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
      </div>
    </nav>
  );
}
