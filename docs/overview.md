<!--
  ~ SPDX-License-Identifier: MIT
  ~ Copyright (c) 2026 Stuart Alldred.
  -->

# Overview

High-level picture of Eumos and how its parts fit together.

## What is Eumos?

Eumos is a **machine-readable RISC-V specification** in Python. The ISA data (instructions, CSRs, GPRs, FPRs, instruction formats) lives in **YAML files** under the package’s `arch/` directory. **Loaders** read and validate these files and produce **Python objects** (instruction definitions, CSR definitions, etc.). You can use a single **Eumos** class that loads everything, or call individual loaders. For execution-oriented use cases, a **Decoder** turns 32-bit opcodes or assembly strings into **InstructionInstance** objects, and instances can be encoded back to opcodes or assembly; optional **RegisterContext** and **CSRContext** add runtime register and CSR values.

## Architecture

YAML under `arch/rv64/` (instructions, csrs, formats, fprs) is validated and loaded by per-domain loaders into model types: `InstructionDef`, `CSRDef`, `FormatDef`, `GPRDef`, `FPRDef`. No config or env; everything comes from the package.

**Entry points:**

- **Eumos** — Calls all loaders; exposes `.instructions`, `.csrs`, `.formats`, `.gprs`, `.fprs`. Use for the full ISA in one object.
- **Decoder** — Takes a dict of instructions; `from_opc(word)` / `from_asm(asm_str)` return **InstructionInstance**; instances support `to_opc()` and `to_asm()` for round-trip.
- **ISA** — Holds optional `instructions` and/or `csrs` (e.g. for decode + CSR resolution). With **RegisterContext** and **CSRContext** you can resolve operand names and CSR values for an instance.

## Where to go next

- [Getting started](getting-started.md) — install, run examples, run tests.
- [Instructions](instructions.md) — loading and using instruction definitions.
- [CSRs](csrs.md) — loading CSRs and using ISA/CSRContext.
- [Decoder and encoding](decoder-and-encoding.md) — decode/encode and InstructionInstance.
- [Registers and context](registers-and-context.md) — GPRs, FPRs, RegisterContext, and operand info.
- [Data and packaging](data-and-packaging.md) — layout of `arch/` and how the package is built.
