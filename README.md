# fpga-project-template

project.toml              # Project config: FPGA part, top module, module list
hdl/<module>/
├── manifest.toml          # Module manifest: sources, deps, sim targets
├── src/                   # RTL source files
├── tb/                    # Testbenches
└── constraints/           # Pin/timing constraints (.xdc)
scripts/
├── common.py              # Shared utilities
├── sim.py                 # Verilator simulation driver
└── build.py               # Vivado synthesis driver

[module]
name = "<name>"

[rtl]
sources = ["src/<name>.sv"]
include_dirs = []

[deps]
modules = []

[constraints]
files = []

[sim.default]
top = "<name>_tb"
sources = ["tb/<name>_tb.sv"]
verilator_flags = []

python fpga.py sim
python fpga.py sim --trace
python fpga.py sim --trace-fst
python fpga.py sim --clean --trace
python fpga.py list 
python fpga.py lint 

python scripts/build.py impl
python scripts/build.py bit
python scripts/build.py synth --gui


