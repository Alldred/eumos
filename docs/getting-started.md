<!--
  ~ SPDX-License-Identifier: MIT
  ~ Copyright (c) 2026 Stuart Alldred.
  -->

# Getting started

Install dependencies, run the examples, and run tests from a clone.

## Prerequisites

- **Python 3.13** or newer
- **[uv](https://docs.astral.sh/uv/)** for dependency management (e.g. `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)

## 1. Enter the project shell

From the project root, start the project shell (sets up the environment and `PYTHONPATH`):

```bash
./bin/shell
```

You're in a subshell with the project root as the working directory.

## 2. Install dependencies

Install all dependencies, including dev tools (pytest, etc.):

```bash
uv sync --extra dev
```

## 3. Run the examples

**Main example** — loads instructions, CSRs, GPRs, FPRs, and formats and prints a short summary:

```bash
uv run python -m example.eumos_example
```

**Assembly and encoding example** — parses assembly strings, decodes opcodes, and does round-trip asm ↔ opcode:

```bash
uv run python -m example.asm_encoding_example
```

Use `uv run` so dependencies (e.g. PyYAML) are on the path.

## 4. Run tests

Run the full test suite:

```bash
uv run pytest
```

- Verbose output: `uv run pytest -v`
- Single file: `uv run pytest tests/test_instance.py`
- With coverage: `uv run pytest --cov=eumos --cov-report=term-missing`
- HTML coverage report: add `--cov-report=html` (output in `htmlcov/`)

## Next steps

- [Overview](overview.md) — architecture and entry points.
- [Documentation index](README.md) — topic index (instructions, CSRs, decoder, etc.).
