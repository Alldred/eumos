<!--
  ~ SPDX-License-Identifier: MIT
  ~ Copyright (c) 2026 Stuart Alldred.
  -->

# Instructions

This page describes how to load and work with RISC-V instruction definitions in Eumos.

## Loading instructions

You can get a dict of all instructions in two ways:

**1. Use the Eumos facade** (loads instructions plus formats, CSRs, GPRs, FPRs):

```python
from eumos import Eumos

eu = Eumos()
# eu.instructions: mnemonic -> InstructionDef
for mnemonic, instr in eu.instructions.items():
    print(instr.mnemonic, instr.description)
```

**2. Use the instruction loader directly** (only instructions and the formats they depend on):

```python
from eumos.instruction_loader import load_all_instructions

instructions = load_all_instructions()
# instructions: mnemonic (e.g. "addi", "sd") -> InstructionDef
addi = instructions["addi"]
```

Each value is an **InstructionDef** (also exposed as `Instruction` in the loader). The loader reads from the built-in `arch/rv64/instructions/` tree and validates with `arch/schemas/instruction_schema.yaml`. See [Data and packaging](data-and-packaging.md) for where data lives.

## InstructionDef

Each **InstructionDef** has (among others):

- **name**, **mnemonic** — e.g. `"addi"`, `"sd"`.
- **format** — A **FormatDef** describing the instruction layout (R, I, S, B, U, J, etc.) and assembly syntax. See below.
- **operands** — Dict of operand name → **Operand** (type, size, optional data). These are the logical inputs (rd, rs1, rs2, imm, etc.).
- **fields** — Dict of field name → **FieldEncoding** (bit ranges or parts for split immediates). Describes how operands and fixed values are encoded in the 32-bit word.
- **fixed_values** — opcode, funct3, funct7, etc., for matching during decode.
- **extension** — e.g. `"I"`, `"M"`, `"F"`, `"D"`.
- **description** — Human-readable description.
- **groups** — List of group tags (e.g. `["alu/arith"]`) for categorisation.

Formats come from [format_loader](data-and-packaging.md#directory-layout): each **FormatDef** has `asm_formats` (assembly operand order and optional `offset_base` for memory operands) and `fields` (bit layout). Encoding details (split immediates for S/B type) use `parts[].bits` and `parts[].operand_bits` in the field definitions.

For **concrete operand values** (decoded or built by hand), use **InstructionInstance** and optional **RegisterContext** from the `instance` module; see [Decoder and encoding](decoder-and-encoding.md) and [Registers and context](registers-and-context.md).

## Instruction groups

Instructions can be tagged with **groups** (e.g. `memory/load`, `alu/arith`, `system/csr`). Use this to filter or categorise.

- **instruction_groups(instructions)** — Returns a sorted list of all distinct group strings present in the instruction dict.
- **instructions_by_group(instructions, group)** — Returns a dict of mnemonic → InstructionDef for instructions that belong to the given group (exact or path-prefix match; e.g. `"alu"` matches `"alu/arith"`).
- **instr.in_group(group)** — Method on InstructionDef: returns True if that instruction is in the group.

Example:

```python
from eumos.instruction_loader import load_all_instructions, instruction_groups, instructions_by_group

all_instrs = load_all_instructions()
groups = instruction_groups(all_instrs)
loads = instructions_by_group(all_instrs, "memory/load")
```

## Related topics

- **Decoding and encoding**: [Decoder and encoding](decoder-and-encoding.md) — turn opcodes or assembly into **InstructionInstance**, and back.
- **Registers and runtime values**: [Registers and context](registers-and-context.md) — **RegisterContext**, **OperandInfo**, and when operand names/values are resolved.
- **Data layout**: [Data and packaging](data-and-packaging.md) — where instruction and format YAML and schemas live.
