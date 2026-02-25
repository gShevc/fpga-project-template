#!/usr/bin/env python3
"""fpga.py -- Top-level CLI for the FPGA project.

Replaces the Makefile. All commands dispatch to scripts/ internally.

Usage:
    python fpga.py new <name> [--deps mod1 mod2]
    python fpga.py sim [target] [-m module] [--trace] [--clean]
    python fpga.py lint [target] [-m module]
    python fpga.py synth [--gui]
    python fpga.py impl [--gui]
    python fpga.py bit [--gui]
    python fpga.py list
    python fpga.py clean
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"


def run_script(name: str, args: list[str]) -> int:
    """Run a script from scripts/ with the given arguments."""
    script = SCRIPTS_DIR / name
    return subprocess.run([sys.executable, str(script)] + args).returncode


def cmd_sim(args):
    fwd = [args.target]
    if args.module:
        fwd += ["--module", args.module]
    if args.trace:
        fwd += ["--trace"]
    if args.trace_fst:
        fwd += ["--trace-fst"]
    if args.clean:
        fwd += ["--clean"]
    return run_script("sim.py", fwd)


def cmd_lint(args):
    fwd = [args.target, "--lint-only"]
    if args.module:
        fwd += ["--module", args.module]
    return run_script("sim.py", fwd)


def cmd_list(args):
    return run_script("sim.py", ["--list"])


def cmd_synth(args):
    fwd = ["synth"]
    if args.gui:
        fwd += ["--gui"]
    return run_script("build.py", fwd)


def cmd_impl(args):
    fwd = ["impl"]
    if args.gui:
        fwd += ["--gui"]
    return run_script("build.py", fwd)


def cmd_bit(args):
    fwd = ["bit"]
    if args.gui:
        fwd += ["--gui"]
    return run_script("build.py", fwd)


def cmd_new(args):
    fwd = [args.name]
    if args.deps:
        fwd += ["--deps"] + args.deps
    return run_script("new_module.py", fwd)


def cmd_clean(args):
    root = Path(__file__).resolve().parent
    # Clean build/
    build_dir = root / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("Removed build/")
    # Clean impl/
    impl_dir = root / "impl"
    if impl_dir.exists():
        shutil.rmtree(impl_dir)
        print("Removed impl/")
    impl_dir.mkdir(exist_ok=True)
    # Clean sim/ directories inside each module (waveforms)
    for sim_dir in (root / "hdl").rglob("sim"):
        if sim_dir.is_dir():
            shutil.rmtree(sim_dir)
            print(f"Removed {sim_dir.relative_to(root)}/")
    print("Clean complete.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="fpga.py",
        description="FPGA project build and simulation tool",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # new
    p = sub.add_parser("new", help="Create a new HDL module")
    p.add_argument("name", help="Module name (e.g. uart, spi, blinker)")
    p.add_argument("--deps", nargs="*", default=[], help="Module dependencies")
    p.set_defaults(func=cmd_new)

    # sim
    p = sub.add_parser("sim", help="Run simulation")
    p.add_argument("target", nargs="?", default="default")
    p.add_argument("-m", "--module", default=None, help="Restrict to a specific module")
    p.add_argument("--trace", action="store_true", help="Enable VCD waveform tracing")
    p.add_argument("--trace-fst", action="store_true", help="Enable FST waveform tracing")
    p.add_argument("--clean", action="store_true", help="Clean before building")
    p.set_defaults(func=cmd_sim)

    # lint
    p = sub.add_parser("lint", help="Run Verilator lint only")
    p.add_argument("target", nargs="?", default="default")
    p.add_argument("-m", "--module", default=None, help="Restrict to a specific module")
    p.set_defaults(func=cmd_lint)

    # list
    p = sub.add_parser("list", help="List all simulation targets")
    p.set_defaults(func=cmd_list)

    # synth
    p = sub.add_parser("synth", help="Run Vivado synthesis")
    p.add_argument("--gui", action="store_true")
    p.set_defaults(func=cmd_synth)

    # impl
    p = sub.add_parser("impl", help="Run Vivado synthesis + implementation")
    p.add_argument("--gui", action="store_true")
    p.set_defaults(func=cmd_impl)

    # bit
    p = sub.add_parser("bit", help="Run full flow through bitstream")
    p.add_argument("--gui", action="store_true")
    p.set_defaults(func=cmd_bit)

    # clean
    p = sub.add_parser("clean", help="Remove all build and simulation artifacts")
    p.set_defaults(func=cmd_clean)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
