<!--
  ~ SPDX-License-Identifier: MIT
  ~ Copyright (c) 2026 Stuart Alldred. All Rights Reserved
  -->

<!-- SPDX-License-Identifier: MIT -->
<!-- Copyright (c) 2026 Stuart Alldred. All Rights Reserved -->

Eumos is a Python-based machine-readable specification for RISC-V.

## Running

Start from the project shell so the environment is set up:

```bash
./bin/shell
```

Then install dependencies (including dev tools like pytest) with uv:

```bash
uv sync --extra dev
```

### Example usage

To see how to use the instruction loader, run the example script (use `uv run` so dependencies like PyYAML are available):

```bash
uv run python -m example.eumos_example
```

This will load instructions from the built-in YAML files and print a summary.

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

## Data model

- **load_all_instructions()** returns a dict: mnemonic (e.g. `"addi"`, `"sd"`) -> **Instruction**.
- Each **Instruction** has: `name`, `mnemonic`, `format` (a **Format**), `operands` (name -> **Operand**), `fields` (name -> **FieldEncoding**), `inputs` (ordered list), `fixed_values` (opcode, funct3, funct7), `imm`, `description`, and `extension`.
- **Format** has `asm_formats` (list of assembly patterns like `"{mnemonic} {rd:reg}, {rs1:reg}, {imm:imm}"`) and `fields` (list of **FieldDef**). Encoding bit ranges come from `fields`; for split immediates (S/B type), use `parts[].bits` and `parts[].operand_bits`.
- For user data (concrete operand values, register names/values), use **InstructionInstance** and **RegisterContext** from `instance`; `get_operand_info(name)` returns **OperandInfo**, which combines ISA and user data per operand.
- **Decoder**: use `decoder.from_opc(word)` to decode a 32-bit instruction opcode into an **InstructionInstance** with `instruction` and `operand_values` filled from the encoding (rd, rs1, rs2, imm, etc.). Use `decoder.from_asm(asm_str)` to parse assembly strings. Without a **RegisterContext**, GPR values and resolved names are not populated; only what can be decoded from the bits is set.

## CSRs

- **load_all_csrs()** (from `csr_loader`) returns a dict: name (e.g. `"mstatus"`, `"mepc"`) -> **CSR**. CSR YAML files are loaded from the built-in `arch/rv64/csrs/` directory and validated by `arch/schemas/csr_file_schema.yaml`.
- **CSR** has `name`, `address` (12-bit), `description`, and optional `privilege`, `access`, `width`, `extension`.
- **ISA** (from `instance`) holds optional `instructions` and/or `csrs`; you can load either or both (e.g. `ISA(instructions=load_all_instructions(), csrs=load_all_csrs())`). When CSRs are loaded, `isa.csrs_by_address` maps 12-bit address -> **CSR** for resolving the `imm` operand of CSR instructions.
- **CSRContext** (from `instance`) maps CSR address or name to runtime values; optionally pass `csr_defs` so that `set`/`get_value` accept names (e.g. `"mstatus"`) and `get_name`/`get_address` work.
- For CSR instructions (e.g. `csrrw`, `csrrs`), the `imm` operand in `operand_values` is the 12-bit CSR address. Use **ISA.resolve_csr(instruction_instance, csr_context)** to get the **CSR** and current value (if a **CSRContext** is provided).

## Data Directory and Packaging

All RISC-V YAML data and schema files are included in the package under the `arch/` directory. Loader functions always load from this built-in location; there is no support for user-specified data directories or environment variables. All schema and data files are included automatically via `pyproject.toml` and `MANIFEST.in`.

If you install Eumos as a package, all required data files are available and no additional configuration is needed.
