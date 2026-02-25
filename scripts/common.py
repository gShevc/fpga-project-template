"""common.py -- Shared utilities for FPGA project scripts."""

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

# Well-known MSYS2 directories to search when tools aren't on the Windows PATH.
_MSYS2_SEARCH_DIRS = [
    Path("C:/msys64/mingw64/bin"),
    Path("C:/msys64/usr/bin"),
]

_MSYS2_BASH = Path("C:/msys64/usr/bin/bash.exe")


def find_project_root() -> Path:
    """Return the directory containing project.toml."""
    candidate = Path(__file__).resolve().parent.parent
    if (candidate / "project.toml").is_file():
        return candidate
    cwd = Path.cwd()
    if (cwd / "project.toml").is_file():
        return cwd
    print("ERROR: Cannot locate project.toml", file=sys.stderr)
    sys.exit(1)


def load_config(root: Path) -> dict:
    """Read and return the parsed project.toml."""
    with open(root / "project.toml", "rb") as f:
        return tomllib.load(f)


def load_module_manifest(module_dir: Path) -> dict:
    """Read and return a module's manifest.toml."""
    manifest_path = module_dir / "manifest.toml"
    if not manifest_path.is_file():
        print(f"ERROR: manifest.toml not found in {module_dir}", file=sys.stderr)
        sys.exit(1)
    with open(manifest_path, "rb") as f:
        return tomllib.load(f)


def resolve_paths(base: Path, paths: list[str]) -> list[Path]:
    """Resolve path strings relative to base into absolute Paths."""
    resolved = []
    for p in paths:
        full = base / p
        if not full.exists():
            print(f"WARNING: listed file does not exist: {full}", file=sys.stderr)
        resolved.append(full)
    return resolved


def resolve_modules(root: Path, cfg: dict) -> list[dict]:
    """Load all module manifests listed in project.toml, respecting dep order.

    Returns a list of dicts, each containing:
        - "dir": Path to the module directory
        - "manifest": parsed manifest.toml dict
    """
    module_paths = cfg.get("project", {}).get("modules", [])
    loaded = []
    seen = set()

    def _load(mod_rel: str):
        if mod_rel in seen:
            return
        seen.add(mod_rel)

        mod_dir = root / mod_rel
        manifest = load_module_manifest(mod_dir)

        # Recursively load dependencies first
        deps = manifest.get("deps", {}).get("modules", [])
        for dep_name in deps:
            # Find the dep in the project module list by matching the module name
            dep_path = _find_module_path(root, cfg, dep_name)
            if dep_path:
                _load(dep_path)
            else:
                print(
                    f"ERROR: module '{mod_rel}' depends on '{dep_name}', "
                    f"which is not listed in project.toml modules",
                    file=sys.stderr,
                )
                sys.exit(1)

        loaded.append({"dir": mod_dir, "manifest": manifest})

    for mod_rel in module_paths:
        _load(mod_rel)

    return loaded


def _find_module_path(root: Path, cfg: dict, module_name: str) -> str | None:
    """Find a module's relative path in project.toml by its manifest name."""
    for mod_rel in cfg.get("project", {}).get("modules", []):
        mod_dir = root / mod_rel
        manifest_path = mod_dir / "manifest.toml"
        if manifest_path.is_file():
            with open(manifest_path, "rb") as f:
                m = tomllib.load(f)
            if m.get("module", {}).get("name") == module_name:
                return mod_rel
    return None


def collect_rtl_sources(root: Path, cfg: dict) -> tuple[list[Path], list[Path]]:
    """Collect all RTL sources and include dirs across all modules.

    Returns (sources, include_dirs) with paths in dependency order.
    """
    modules = resolve_modules(root, cfg)
    sources = []
    include_dirs = []

    for mod in modules:
        mod_dir = mod["dir"]
        rtl = mod["manifest"].get("rtl", {})
        sources.extend(resolve_paths(mod_dir, rtl.get("sources", [])))
        include_dirs.extend(resolve_paths(mod_dir, rtl.get("include_dirs", [])))

    return sources, include_dirs


def collect_constraints(root: Path, cfg: dict) -> list[Path]:
    """Collect all constraint files across all modules."""
    modules = resolve_modules(root, cfg)
    constraints = []

    for mod in modules:
        mod_dir = mod["dir"]
        cons = mod["manifest"].get("constraints", {})
        constraints.extend(resolve_paths(mod_dir, cons.get("files", [])))

    return constraints


def collect_sim_target(
    root: Path, cfg: dict, target: str, module_name: str | None = None
) -> dict | None:
    """Find a simulation target across modules.

    If module_name is given, only search that module.
    Returns a dict with keys: top, sources, include_dirs, verilator_flags, mod_dir.
    Returns None if not found.
    """
    modules = resolve_modules(root, cfg)
    global_flags = cfg.get("sim", {}).get("verilator_flags", [])

    for mod in modules:
        mod_dir = mod["dir"]
        manifest = mod["manifest"]
        name = manifest.get("module", {}).get("name", "")

        if module_name and name != module_name:
            continue

        sim_targets = manifest.get("sim", {})
        if target in sim_targets:
            tcfg = sim_targets[target]

            # RTL sources from this module + its deps
            rtl_sources, rtl_inc_dirs = _collect_rtl_for_module(root, cfg, mod)

            # Sim-specific sources (testbenches)
            sim_sources = resolve_paths(mod_dir, tcfg.get("sources", []))

            # Sim-specific include dirs
            sim_inc_dirs = resolve_paths(mod_dir, tcfg.get("include_dirs", []))

            # Merge: RTL sources first, then testbench sources
            all_sources = rtl_sources + sim_sources
            all_inc_dirs = rtl_inc_dirs + sim_inc_dirs

            # Merge verilator flags: global + per-target
            flags = list(global_flags) + tcfg.get("verilator_flags", [])

            return {
                "top": tcfg["top"],
                "sources": all_sources,
                "include_dirs": all_inc_dirs,
                "verilator_flags": flags,
                "module": name,
                "mod_dir": mod_dir,
            }

    return None


def list_sim_targets(root: Path, cfg: dict) -> list[str]:
    """List all available simulation targets as 'module.target' strings."""
    modules = resolve_modules(root, cfg)
    targets = []
    for mod in modules:
        name = mod["manifest"].get("module", {}).get("name", "?")
        sim = mod["manifest"].get("sim", {})
        for t in sim:
            targets.append(f"{name}.{t}")
    return targets


def _collect_rtl_for_module(
    root: Path, cfg: dict, mod: dict
) -> tuple[list[Path], list[Path]]:
    """Collect RTL sources for a module and all its dependencies."""
    all_modules = resolve_modules(root, cfg)
    manifest = mod["manifest"]
    mod_name = manifest.get("module", {}).get("name", "")

    # Find this module and all its transitive deps
    dep_names = _transitive_deps(root, cfg, mod_name)
    dep_names.append(mod_name)

    sources = []
    include_dirs = []
    for m in all_modules:
        mname = m["manifest"].get("module", {}).get("name", "")
        if mname in dep_names:
            rtl = m["manifest"].get("rtl", {})
            sources.extend(resolve_paths(m["dir"], rtl.get("sources", [])))
            include_dirs.extend(resolve_paths(m["dir"], rtl.get("include_dirs", [])))

    return sources, include_dirs


def _transitive_deps(root: Path, cfg: dict, module_name: str) -> list[str]:
    """Return a flat list of all transitive dependency names for a module."""
    result = []
    visited = set()

    def _walk(name: str):
        if name in visited:
            return
        visited.add(name)
        mod_rel = _find_module_path(root, cfg, name)
        if not mod_rel:
            return
        mod_dir = root / mod_rel
        manifest = load_module_manifest(mod_dir)
        for dep in manifest.get("deps", {}).get("modules", []):
            _walk(dep)
            if dep not in result:
                result.append(dep)

    _walk(module_name)
    return result


# ---------------------------------------------------------------------------
# Tool detection and subprocess execution (MSYS2-aware)
# ---------------------------------------------------------------------------

def require_tool(name: str, hint: str = "") -> Path:
    """Find a tool on PATH or in well-known MSYS2 locations."""
    exe = shutil.which(name)
    if exe is not None:
        return Path(exe)

    for d in _MSYS2_SEARCH_DIRS:
        candidate = d / name
        if candidate.is_file():
            return candidate
        candidate_exe = candidate.with_suffix(".exe")
        if candidate_exe.is_file():
            return candidate_exe

    msg = f"ERROR: '{name}' not found on PATH."
    if hint:
        msg += f" {hint}"
    print(msg, file=sys.stderr)
    sys.exit(1)


def _to_msys2_path(p: str) -> str:
    """Convert a Windows path to MSYS2 Unix-style path.

    C:\\Users\\foo  ->  /c/Users/foo
    C:/Users/foo   ->  /c/Users/foo
    """
    s = str(p).replace("\\", "/")
    if len(s) >= 2 and s[1] == ":":
        s = "/" + s[0].lower() + s[2:]
    return s


def _needs_msys2(exe: Path) -> bool:
    """Return True if the executable is an extensionless script requiring MSYS2."""
    return (
        os.name == "nt"
        and exe.suffix == ""
        and exe.is_file()
        and _MSYS2_BASH.is_file()
    )


def run(cmd: list[str], *, cwd: Path | None = None, env=None) -> None:
    """Run a subprocess, streaming output. Exit on failure.

    On Windows, if the executable is an extensionless script (e.g. a Perl
    wrapper like verilator), it is invoked through the MSYS2 bash shell
    with all paths converted to Unix-style so MSYS2 tools can resolve them.
    """
    exe = Path(cmd[0])

    if _needs_msys2(exe):
        unix_cmd = [_to_msys2_path(c) for c in cmd]
        unix_cwd = _to_msys2_path(cwd) if cwd else None

        shell_cmd = " ".join(f"'{c}'" for c in unix_cmd)
        if unix_cwd:
            shell_cmd = f"cd '{unix_cwd}' && {shell_cmd}"

        # MSYSTEM=MINGW64 ensures bash -l adds /mingw64/bin to PATH,
        # which is needed for g++, make, python3, etc.
        msys_env = os.environ.copy()
        msys_env["MSYSTEM"] = "MINGW64"

        final_cmd = [str(_MSYS2_BASH), "-lc", shell_cmd]
        print(f">> {' '.join(unix_cmd)}")
        result = subprocess.run(final_cmd, env=msys_env)
    else:
        if env is None:
            env = os.environ.copy()
            for d in _MSYS2_SEARCH_DIRS:
                if d.is_dir():
                    env["PATH"] = str(d) + os.pathsep + env.get("PATH", "")
        print(f">> {' '.join(str(c) for c in cmd)}")
        result = subprocess.run(cmd, cwd=cwd, env=env)

    if result.returncode != 0:
        print(f"ERROR: command exited with code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
