<!--
  ~ SPDX-License-Identifier: MIT
  ~ Copyright (c) 2026 Stuart Alldred.
  -->

# Decoder and encoding

This page describes how to decode RISC-V instruction words or assembly strings into **InstructionInstance** objects, and how to encode instances back to assembly or 32-bit opcodes.

## Decoder

The **Decoder** (in `eumos.decoder`) needs a dict of mnemonic → **InstructionDef**, usually from `load_all_instructions()`:

```python
from eumos.instruction_loader import load_all_instructions
from eumos.decoder import Decoder

instructions = load_all_instructions()
decoder = Decoder(instructions)
```

### Decode from opcode

**from_opc(word)** decodes a 32-bit instruction word into an **InstructionInstance** with `instruction` and `operand_values` filled from the encoding (rd, rs1, rs2, imm, etc.):

```python
instance = decoder.from_opc(0x005211B3)  # sll x3, x4, x5
print(instance.instruction.mnemonic)   # "sll"
print(instance.operand_values)         # e.g. {"rd": 3, "rs1": 4, "rs2": 5}
print(instance.to_asm())               # "sll x3, x4, x5"
```

Without a **RegisterContext**, only what can be decoded from the bits is set (register indices, immediates); GPR/FPR values and resolved ABI names are not populated. See [Registers and context](registers-and-context.md).

### Decode from assembly

**from_asm(asm_str)** parses an assembly string and returns an **InstructionInstance**:

```python
instance = decoder.from_asm("addi x1, x2, 4")
print(instance.instruction.mnemonic)   # "addi"
print(instance.operand_values)         # {"rd": 1, "rs1": 2, "imm": 4}
print(instance.to_opc())               # 32-bit opcode
```

Register operands can be given as `xN`/`fN` or ABI names (e.g. `ra`, `sp`).

## InstructionInstance

An **InstructionInstance** (from `eumos.instance`) represents one concrete instruction with bound operand values. It has:

- **instruction** — The **InstructionDef** (mnemonic, format, operands, etc.).
- **operand_values** — Dict of operand name → value (register index, immediate, etc.).
- Optional **register_context**, **csr_context**, **pc** for richer resolution (see [Registers and context](registers-and-context.md)).

**to_asm()** — Returns the assembly string for this instance (e.g. `"addi x1, x2, 4"`).

**to_opc()** — Packs the instance into a 32-bit opcode using the instruction’s encoding.

You can also build an instance by hand:

```python
from eumos.instance import InstructionInstance

jalr = instructions["jalr"]
instance = InstructionInstance(
    instruction=jalr,
    operand_values={"rd": 0, "rs1": 2, "imm": 0},
)
print(instance.to_asm())
print(hex(instance.to_opc()))
```

## Round-trip: assembly ↔ opcode

You can round-trip from assembly to opcode and back:

```python
asm = "sd x6, 8(x7)"
inst = decoder.from_asm(asm)
opcode = inst.to_opc()
decoded = decoder.from_opc(opcode)
assert decoded.to_asm() == asm
```

## Example script

Parsing, encoding, and decoding:

```bash
uv run python -m example.asm_encoding_example
```

Code: [example/asm_encoding_example.py](../example/asm_encoding_example.py).

## Related topics

- **Instruction definitions**: [Instructions](instructions.md).
- **Register and CSR context**: [Registers and context](registers-and-context.md).
- **CSR resolution**: [CSRs](csrs.md) — resolving the CSR for CSR instructions via **ISA.resolve_csr**.
