<!--
  ~ SPDX-License-Identifier: MIT
  ~ Copyright (c) 2026 Stuart Alldred.
  -->

Eumos is a Python-based machine-readable specification for RISC-V.

## What is Eumos?

Eumos provides a machine-readable RISC-V specification: instructions, CSRs, GPRs, FPRs, and instruction formats are defined in YAML and loaded into Python. You get loaders for all of this data, a decoder and encoder for instruction words and assembly, and optional runtime context (register and CSR values). Requires Python 3.13+; dependencies are managed with [uv](https://docs.astral.sh/uv/).

## Quick start

From the project root, run the project shell to set up the environment:

```bash
./bin/shell
```

Install dependencies (including dev tools like pytest):

```bash
uv sync --extra dev
```

Run the main example to load and inspect instructions, CSRs, and formats:

```bash
uv run python -m example.eumos_example
```

For assembly parsing, encoding, and decoding:

```bash
uv run python -m example.asm_encoding_example
```

## Documentation

[docs/](docs/) — architecture, API usage, and topic guides.

## Running

### Tests

Run all tests:

```bash
uv run pytest
```

Use `uv run pytest -v` for verbose, or `uv run pytest tests/test_instance.py` to run a single file.

### Coverage

Run tests with code coverage:

```bash
uv run pytest --cov=eumos --cov-report=term-missing
```

Add `--cov-report=html` to generate an HTML report in `htmlcov/`.

## At a glance

- **Instructions**: `load_all_instructions()` (or `Eumos().instructions`) returns mnemonic → **Instruction**; each instruction has format, operands, fields, and encoding info.
- **Decode and encode**: **Decoder** (`from_opc(word)`, `from_asm(asm_str)`) and **InstructionInstance** (`to_asm()`, `to_opc()`) for round-trip between assembly and opcode.
- **Runtime**: **ISA** holds instructions and/or CSRs; **RegisterContext** and **CSRContext** (from `instance`) provide register and CSR values; **InstructionInstance** and `get_operand_info()` combine ISA and context.

See [docs/](docs/) for full details.

## Data directory and packaging

All RISC-V YAML data and schema files are included in the package under the `arch/` directory. Loader functions always load from this built-in location; there is no support for user-specified data directories or environment variables. All schema and data files are included automatically via `pyproject.toml` and `MANIFEST.in`.

If you install Eumos as a package, all required data files are available and no additional configuration is needed.
