<!--
  ~ SPDX-License-Identifier: MIT
  ~ Copyright (c) 2026 Stuart Alldred.
  -->

# Data and packaging

Where architecture data lives, how it is validated, and how the package is built.

## Built-in data only

All RISC-V YAML data and schema files are **included in the package** under the `eumos/arch/` directory. Loader functions always read from this built-in location. There is no support for user-specified data directories or environment variables. After `pip install .` or `uv pip install -e .`, all data files are available and no configuration is needed.

## Directory layout

Under `eumos/arch/`:

- **arch/schemas/** — YAML schemas used to validate data files (e.g. `instruction_schema.yaml`, `csr_schema.yaml`, `format_schema.yaml`, `gpr_file_schema.yaml`, `fpr_file_schema.yaml`).
- **arch/rv64/** — RV64G-style data:
  - **instructions/** — One YAML file per instruction (or group), organised in subdirectories by extension (e.g. I, M, F, D). Loaded by `instruction_loader`; validated with `instruction_schema.yaml`.
  - **csrs/** — One YAML file per CSR (e.g. `mstatus.yml`, `mepc.yml`). Loaded by `csr_loader`; validated with `csr_schema.yaml`.
  - **formats/** — Instruction format definitions (R, I, S, B, U, J, R4, etc.). Loaded by `format_loader`; validated with `format_schema.yaml`.
  - **fprs/** — Floating-point register definitions (f0–f31). Loaded by `fpr_loader`; validated with `fpr_file_schema.yaml`.

GPR definitions are loaded from a built-in path inside the package (see `gpr_loader`). Exception cause definitions are loaded from a built-in path (see `exception_loader`).

## Packaging

- **pyproject.toml** — Declares package data with `[tool.setuptools.package-data]` so that `eumos = ["arch/**/*"]` is included in the wheel/sdist.
- **MANIFEST.in** — Contains `recursive-include eumos/arch *` so that all files under `eumos/arch/` are included in the source distribution.

With this setup, `pip install .` or `uv pip install -e .` makes the `arch/` tree available as part of the installed package, and the loaders (which use paths relative to the package) find it without any environment variables or user configuration.

## Related topics

- [Overview](overview.md) — How loaders and data fit into the overall design.
- [Getting started](getting-started.md) — Install and run from a development clone.
