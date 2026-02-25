What was created
Manifest & Config

project.toml — Central manifest declaring FPGA part, source files, constraints, and simulation targets. Edit this file to configure any new project.
HDL Sources

hdl/src/top.sv — Example LED blinker (4-bit rotating pattern at ~1 Hz)
hdl/tb/top_tb.sv — Verilator-compatible testbench with clock gen, reset, assertion, and timeout watchdog
hdl/constraints/pins.xdc — Example Arty A7-35T pin constraints
hdl/include/ — Empty directory for SV packages/headers
Build Scripts

scripts/common.py — Shared utilities (TOML parsing, tool detection, subprocess wrapper)
scripts/sim.py — Verilator driver (--binary mode, --trace, --lint-only)
scripts/build.py — Vivado driver (generates TCL on the fly, non-project mode)
Orchestration

Makefile — Convenience targets: sim, lint, synth, impl, bit, program, clean
.gitignore — Ignores build artifacts, sim outputs, venv, Vivado files
How to use
Command	What it does
make sim	Compile & run default testbench with Verilator
make sim TRACE=1	Same but generate VCD waveform
make sim TARGET=name	Run a specific [sim.name] target
make lint	Verilator lint check (no simulation)
make synth	Vivado synthesis only
make impl	Synthesis + place & route
make bit	Full flow through bitstream
make clean	Remove all build/sim artifacts
Scripts also work standalone: python scripts/sim.py default --trace or python scripts/build.py synth --gui.

To reuse as a template: copy the directory, edit projec