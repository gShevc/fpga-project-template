"""new_module.py -- Scaffold a new HDL module.

Creates the directory structure, starter RTL/testbench files, and
manifest.toml for a new module under hdl/.

Usage:
    python scripts/new_module.py <name> [--deps mod1 mod2]
"""

import argparse
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_project_root


def main():
    parser = argparse.ArgumentParser(description="Create a new HDL module")
    parser.add_argument("name", help="Module name (e.g. uart, spi, blinker)")
    parser.add_argument(
        "--deps", nargs="*", default=[], help="Module dependencies by name"
    )
    args = parser.parse_args()

    name = args.name
    root = find_project_root()
    mod_dir = root / "hdl" / name

    if mod_dir.exists():
        print(f"ERROR: {mod_dir.relative_to(root)} already exists", file=sys.stderr)
        sys.exit(1)

    # Create directory structure
    (mod_dir / "src").mkdir(parents=True)
    (mod_dir / "tb").mkdir(parents=True)

    # Write starter RTL source
    src_file = mod_dir / "src" / f"{name}.sv"
    src_file.write_text(
        f"""`timescale 1ns / 1ps

module {name} (
    input  logic clk,
    input  logic rst_n
);

    // TODO: implement {name}

endmodule
""",
        encoding="utf-8",
    )

    # Write starter testbench
    tb_file = mod_dir / "tb" / f"{name}_tb.sv"
    tb_file.write_text(
        f"""`timescale 1ns / 1ps

module {name}_tb;

    logic clk;
    logic rst_n;

    {name} dut (
        .clk   (clk),
        .rst_n (rst_n)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    initial begin
        $dumpfile("{name}_tb.vcd");
        $dumpvars(0, {name}_tb);

        rst_n = 1'b0;
        repeat (10) @(posedge clk);
        rst_n = 1'b1;

        repeat (200) @(posedge clk);
        $finish;
    end

endmodule
""",
        encoding="utf-8",
    )

    # Write manifest.toml
    deps_list = "\n".join(f'    "{d}",' for d in args.deps)
    deps_section = f"[\n{deps_list}\n]" if args.deps else "[]"

    manifest = mod_dir / "manifest.toml"
    manifest.write_text(
        f"""[module]
name = "{name}"

[rtl]
sources = [
    "src/{name}.sv",
]
include_dirs = []

[deps]
modules = {deps_section}

[sim.default]
top = "{name}_tb"
sources = [
    "tb/{name}_tb.sv",
]
verilator_flags = []
""",
        encoding="utf-8",
    )

    # Add module to project.toml modules list
    proj_toml = root / "project.toml"
    with open(proj_toml, "rb") as f:
        cfg = tomllib.load(f)

    mod_rel = f"hdl/{name}"
    modules = cfg.get("project", {}).get("modules", [])
    if mod_rel not in modules:
        text = proj_toml.read_text(encoding="utf-8")
        # Insert new module before the closing bracket of the modules array
        old = f'    "hdl/top",\n]'
        # Find the last entry to append after it
        lines = text.splitlines(keepends=True)
        new_lines = []
        inserted = False
        for line in lines:
            new_lines.append(line)
            if not inserted and line.strip().startswith('"hdl/') and line.rstrip().endswith(","):
                # Check if next non-blank line is ']' — if so, insert before it
                pass
            if not inserted and line.strip() == "]" and any(
                '"hdl/' in prev for prev in new_lines[-5:]
            ):
                # Insert before this closing bracket
                new_lines.insert(-1, f'    "{mod_rel}",\n')
                inserted = True

        if inserted:
            proj_toml.write_text("".join(new_lines), encoding="utf-8")
            print(f"Added '{mod_rel}' to project.toml modules")
        else:
            print(
                f"WARNING: could not auto-add '{mod_rel}' to project.toml. "
                f"Add it manually to the modules list.",
                file=sys.stderr,
            )

    print(f"Created module '{name}':")
    print(f"  {mod_dir.relative_to(root)}/src/{name}.sv")
    print(f"  {mod_dir.relative_to(root)}/tb/{name}_tb.sv")
    print(f"  {mod_dir.relative_to(root)}/manifest.toml")


if __name__ == "__main__":
    main()
