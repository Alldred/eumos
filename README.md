<!--
  ~ SPDX-License-Identifier: MIT
  ~ Copyright (c) 2026 Stuart Alldred. All Rights Reserved
  -->

Slate is a python-based machine readable specification for RISCV.

Will be very basic/limited to begin with, but will be adding more extensions and information over time.

## Running

Start from the project shell so the environment is set up:

```bash
./bin/shell
```

Then install dependencies (including dev tools like pytest) with uv and run the loader or tests:

```bash
uv sync --extra dev
python3 python/instruction_loader.py
uv run pytest
```

- **Loader**: `python3 python/instruction_loader.py` prints a sample instruction (SD).
- **Tests**: `uv run pytest` runs all tests. Use `uv run pytest -v` for verbose, or `uv run pytest tests/test_instance.py` to run a single file.
- **Coverage**: `uv run pytest --cov=python --cov-report=term-missing` runs tests with code coverage and shows which lines are not covered. Add `--cov-report=html` to generate an HTML report in `htmlcov/`.

## Data model

- **load_all_instructions()** returns a dict: mnemonic (e.g. `"addi"`, `"sd"`) -> **InstructionDef**.
- Each **InstructionDef** has: `name`, `mnemonic`, `format` (a **FormatDef**), `operands` (name -> **Operand**), `fields` (name -> **FieldEncoding**), `inputs` (ordered list), `fixed_values` (opcode, funct3, funct7), `imm`, `description`, and `extension`.
- **FormatDef** has `asm_format` (e.g. `"{mnemonic} {rd}, {rs1}, {imm}"`) and `fields` (list of **FieldDef**). Encoding bit ranges come from `fields`; for split immediates (S/B type), use `parts[].bits` and `parts[].operand_bits`.
- For user data (concrete operand values, register names/values), use **InstructionInstance** and **RegisterContext** from `instance`; `get_operand_info(name)` returns **OperandInfo**, which combines ISA and user data per operand.
- **Decoder**: use **decoder.Decoder** or **decoder.decode(word)** to decode a 32-bit instruction word into an **InstructionInstance** with `instruction` and `operand_values` filled from the encoding (rd, rs1, rs2, imm, etc.). Without a **RegisterContext**, GPR values and resolved names are not populated; only what can be decoded from the bits is set.
