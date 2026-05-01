"""Validate and register user-submitted reward function snippets.

Safety model: AST-level whitelist + subprocess isolation (training already runs
in ProcessPoolExecutor, which provides an additional boundary).

Custom rewards are persisted to disk (JSON) so that subprocess workers (spawned
via ProcessPoolExecutor on Windows) can load them.
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
from pathlib import Path

from app.config import settings

_BUILTIN_NAMES = set(dir(builtins))

_PERSIST_PATH = Path(settings.data_dir) / "custom_rewards.json"

# ── Whitelist ──────────────────────────────────────────────────────────────────

ALLOWED_BUILTINS = {
    "abs", "min", "max", "sum", "len", "range", "enumerate", "zip",
    "int", "float", "bool", "str", "list", "dict", "tuple", "set",
    "True", "False", "None",
    "print",  # harmless in subprocess
}

ALLOWED_AST_NODES = {
    ast.Module, ast.FunctionDef, ast.arguments, ast.arg,
    ast.Return, ast.Assign, ast.AugAssign,
    ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.If, ast.IfExp,
    ast.Name, ast.Constant, ast.Attribute,
    ast.Call, ast.Expr, ast.Pass, ast.Break, ast.Continue,
    ast.For, ast.While,
    ast.Load, ast.Store,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
    ast.USub, ast.UAdd, ast.Not, ast.Invert,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.And, ast.Or,
    ast.Tuple, ast.List, ast.Dict, ast.Subscript, ast.Slice,
    ast.Index,  # Python < 3.9 compat
    ast.Starred,
    ast.keyword,
    ast.Import, ast.ImportFrom, ast.alias,
}

# Allowed imports (top-level modules or specific submodules)
ALLOWED_IMPORTS = {
    "math",
    "numpy",
    "numpy.linalg",
}

EXPECTED_FN_NAME = "reward_fn"
EXPECTED_PARAMS = ["obs", "reward", "terminated", "truncated"]

# ── Registry ──────────────────────────────────────────────────────────────────

_custom_rewards: dict[str, dict] = {}


def _load_persisted() -> None:
    """Restore custom rewards from disk (for subprocess visibility on Windows)."""
    if _PERSIST_PATH.exists():
        try:
            data = json.loads(_PERSIST_PATH.read_text("utf-8"))
            _custom_rewards.update(data)
        except (json.JSONDecodeError, OSError):
            pass


def _save_persisted() -> None:
    """Write custom rewards to disk."""
    _PERSIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PERSIST_PATH.write_text(json.dumps(_custom_rewards, ensure_ascii=False), "utf-8")


def register(code: str, name: str = "") -> str:
    """Validate and register a custom reward function. Returns reward_id."""
    validate(code)
    rid = _hash(code)
    _custom_rewards[rid] = {"code": code, "name": name or f"custom_{rid[:6]}"}
    _save_persisted()
    return rid


def get(rid: str) -> dict | None:
    return _custom_rewards.get(rid)


def list_custom() -> list[dict]:
    return [{"reward_id": rid, **info} for rid, info in _custom_rewards.items()]


def remove(rid: str) -> bool:
    if rid in _custom_rewards:
        del _custom_rewards[rid]
        _save_persisted()
        return True
    return False


# Restore persisted custom rewards on import (critical for subprocess visibility)
_load_persisted()


# ── Validation ────────────────────────────────────────────────────────────────


def validate(code: str) -> None:
    """Raise ValueError if code is not a valid, safe reward function."""
    if not code or not code.strip():
        raise ValueError("Code must not be empty")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Syntax error: {e}") from e

    nodes = list(ast.walk(tree))

    func_defs = [n for n in nodes if isinstance(n, ast.FunctionDef)]
    if len(func_defs) != 1:
        raise ValueError(
            f"Code must contain exactly one function definition, found {len(func_defs)}"
        )

    fn = func_defs[0]
    if fn.name != EXPECTED_FN_NAME:
        raise ValueError(
            f"Function must be named '{EXPECTED_FN_NAME}', got '{fn.name}'"
        )

    param_names = [a.arg for a in fn.args.args]
    if param_names != EXPECTED_PARAMS:
        raise ValueError(
            f"Function signature must be ({', '.join(EXPECTED_PARAMS)}), "
            f"got ({', '.join(param_names)})"
        )

    # AST node whitelist check
    for node in nodes:
        node_type = type(node)
        if node_type.__name__ in ("Load", "Store", "Del", "Param"):
            continue
        if node_type not in ALLOWED_AST_NODES:
            raise ValueError(
                f"Disallowed syntax: {node_type.__name__} "
                f"(line {getattr(node, 'lineno', '?')})"
            )

    # Builtin usage check
    for node in nodes:
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in _BUILTIN_NAMES and node.id not in ALLOWED_BUILTINS:
                raise ValueError(f"Disallowed builtin: '{node.id}'")

    # Import check
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in {n.split(".")[0] for n in ALLOWED_IMPORTS}:
                    raise ValueError(f"Disallowed import: '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            root = mod.split(".")[0]
            if root not in {n.split(".")[0] for n in ALLOWED_IMPORTS}:
                raise ValueError(f"Disallowed import from: '{mod}'")


def _hash(code: str) -> str:
    return f"C_{hashlib.sha256(code.encode()).hexdigest()[:12]}"
