<!--
  ~ SPDX-License-Identifier: MIT
  ~ Copyright (c) 2026 Stuart Alldred.
  -->

# Eumos documentation

Guides for [Eumos](../README.md): what it is, how to get started, and how to use the APIs.

## Documentation index

| Document | When to read it |
|----------|------------------|
| [Getting started](getting-started.md) | Install, run examples, run tests. |
| [Overview](overview.md) | Data flow, main components, how they fit together. |
| [Instructions](instructions.md) | Load and work with instruction definitions (mnemonics, formats, operands, fields, groups). |
| [CSRs](csrs.md) | Load CSRs, build an ISA with CSRs, resolve CSR instructions with runtime values. |
| [Decoder and encoding](decoder-and-encoding.md) | Decode opcodes to assembly, parse assembly to opcodes, round-trip encode/decode. |
| [Registers and context](registers-and-context.md) | GPR/FPR definitions, register or CSR context, operand info (ISA + runtime values). |
| [Data and packaging](data-and-packaging.md) | Where YAML data lives, schemas, how the package is built. |

## Quick links

- **Run examples and tests**: [Getting started](getting-started.md).
- **Architecture**: [Overview](overview.md), then the topic you need (instructions, CSRs, decoder, etc.).
- **API usage**: Each topic doc has code and cross-links (instructions, CSRs, decoder, registers).
