"""sim.py -- Verilator simulation driver.

Reads per-module simulation targets from manifest.toml files and runs
Verilator in --binary mode.

Usage:
    python scripts/sim.py [target] [--module name] [--trace] [--lint-only] [--clean]
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    find_project_root,
    load_config,
    collect_sim_target,
    list_sim_targets,
    require_tool,
    run,
)


def main():
    parser = argparse.ArgumentParser(description="Run Verilator simulation")
    parser.add_argument(
        "target",
        nargs="?",
        default="default",
        help="Simulation target name from [sim.<target>] in a module manifest",
    )
    parser.add_argument(
        "--module", "-m",
        default=None,
        help="Restrict to a specific module (by name in manifest.toml)",
    )
    parser.add_argument(
        "--trace", action="store_true", help="Enable VCD waveform tracing"
    )
    parser.add_argument(
        "--trace-fst", action="store_true", help="Enable FST waveform tracing"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Remove sim build directory before compiling"
    )
    parser.add_argument(
        "--lint-only", action="store_true", help="Run Verilator lint only (no simulation)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all available simulation targets"
    )
    args = parser.parse_args()

    root = find_project_root()
    cfg = load_config(root)

    if args.list:
        targets = list_sim_targets(root, cfg)
        if targets:
            print("Available simulation targets:")
            for t in targets:
                print(f"  {t}")
        else:
            print("No simulation targets found.")
        return

    # Resolve the simulation target
    sim = collect_sim_target(root, cfg, args.target, module_name=args.module)
    if sim is None:
        available = list_sim_targets(root, cfg)
        avail_str = ", ".join(available) if available else "(none)"
        scope = f" in module '{args.module}'" if args.module else ""
        print(
            f"ERROR: sim target '{args.target}'{scope} not found. "
            f"Available: {avail_str}",
            file=sys.stderr,
        )
        sys.exit(1)

    top = sim["top"]
    sources = sim["sources"]
    inc_dirs = sim["include_dirs"]
    extra_flags = sim["verilator_flags"]
    module_name = sim["module"]

    verilator = require_tool(
        "verilator", hint="Install Verilator (>=5.0 recommended)."
    )

    mod_dir = sim["mod_dir"]
    sim_dir = mod_dir / "sim" / args.target
    if args.clean and sim_dir.exists():
        shutil.rmtree(sim_dir)
    sim_dir.mkdir(parents=True, exist_ok=True)

    # Build Verilator command
    cmd = [str(verilator)]

    if args.lint_only:
        cmd += ["--lint-only"]
    else:
        cmd += ["--binary"]

    cmd += ["-sv", "--top-module", top]
    cmd += ["-Mdir", str(sim_dir)]

    if args.trace:
        cmd += ["--trace"]
    elif args.trace_fst:
        cmd += ["--trace-fst"]

    for inc in inc_dirs:
        cmd += [f"+incdir+{inc}"]

    cmd += extra_flags
    cmd += [str(s) for s in sources]

    run(cmd, cwd=sim_dir)

    if args.lint_only:
        print("Lint passed.")
        return

    # Run the compiled binary
    binary = sim_dir / f"V{top}"
    if os.name == "nt":
        binary = binary.with_suffix(".exe")

    if not binary.exists():
        print(f"ERROR: expected binary not found: {binary}", file=sys.stderr)
        sys.exit(1)

    print(f"\n=== Running simulation: {module_name}.{args.target} ({binary.name}) ===\n")
    run([str(binary)], cwd=sim_dir)

    # Report waveform location
    for ext in (".vcd", ".fst"):
        for waveform in sim_dir.glob(f"*{ext}"):
            print(f"\nWaveform: {waveform}")


if __name__ == "__main__":
    main()
