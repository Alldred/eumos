<!--
  ~ SPDX-License-Identifier: MIT
  ~ Copyright (c) 2026 Stuart Alldred.
  -->

# Registers and context

This page describes GPR and FPR definitions, **RegisterContext** and **CSRContext**, and how **InstructionInstance** combines ISA data with runtime values to give you **OperandInfo** per operand.

## GPR and FPR definitions

**GPRs** (general-purpose integer registers x0–x31) and **FPRs** (floating-point registers f0–f31) have definitions that describe reset value, access, and ABI names.

**Load GPRs:**

```python
from eumos import Eumos, load_all_gprs

# Via Eumos
eu = Eumos()
# eu.gprs: index (0..31) -> GPRDef

# Or via loader
from eumos.gpr_loader import load_all_gprs
gprs = load_all_gprs()
```

**Load FPRs:**

```python
from eumos import Eumos, load_all_fprs

eu = Eumos()
# eu.fprs: index (0..31) -> FPRDef

# Or via loader
from eumos.fpr_loader import load_all_fprs
fprs = load_all_fprs()
```

**GPRDef** / **FPRDef** provide fields such as index, ABI name, reset value, and access. You can also resolve definitions for a single index without loading everything via **get_gpr_def(reg_index)** and **get_fpr_def(reg_index)** in `eumos.instance` (they load on first use).

## RegisterContext (GPR)

**RegisterContext** (in `eumos.instance`) maps GPR index (0..31) to an optional display name and optional value. Attach it to an **InstructionInstance** to get **resolved** names and values for GPR operands in **OperandInfo** (e.g. ABI name "ra" and a concrete value).

```python
from eumos.instance import RegisterContext
from eumos import load_all_gprs

gpr_defs = load_all_gprs()
ctx = RegisterContext(gpr_defs=gpr_defs.values())
ctx.set(1, value=0x80000000)
ctx.set("sp", value=0x90000000)
name = ctx.get_name(1)
value = ctx.get_value(2)
reset = ctx.get_reset_value(0)
```

- **set(reg, name=..., value=...)** — `reg` can be index (0..31) or RISC-V name (e.g. `"ra"`, `"x1"`).
- **get_name(reg_index)** — User-set name or default ABI name (e.g. `"ra"`).
- **get_value(reg_index)** — User-set value, or None.
- **get_reset_value(reg_index)** / **get_access(reg_index)** — From GPR definition if available.

Pass **register_context** when building or decoding an **InstructionInstance** so that **get_operand_info** can fill **resolved_name** and **resolved_value** for GPR operands.

## CSRContext

**CSRContext** maps CSR address (or name, if you pass CSR definitions) to runtime values. It is documented in [CSRs](csrs.md). Use it with **ISA.resolve_csr** for CSR instructions; it does not affect **get_operand_info** for GPR/FPR operands.

## InstructionInstance and get_operand_info

An **InstructionInstance** can optionally hold a **register_context**. When present, **get_operand_info(name)** returns an **OperandInfo** that combines:

- ISA side: **name**, **type**, **size**, **bits** / **parts** (encoding).
- Decoded/user value: **value** (from **operand_values**).
- Resolved (when context is set and operand is a register): **resolved_name** (e.g. ABI name), **resolved_value** (from RegisterContext).

Without a **RegisterContext**, only what can be decoded from the instruction is available: **operand_values** contain register indices and immediates, and **resolved_name** / **resolved_value** in OperandInfo stay None. So:

- **Decode-only**: Use **Decoder().from_opc(word)** or **from_asm(asm_str)** without attaching a context; you get correct **instruction** and **operand_values** (indices, imm), and **to_asm()** / **to_opc()** work. No register values or ABI names in OperandInfo.
- **With context**: Build or decode an instance, then set **register_context** (and optionally use the same instance with **ISA** + **CSRContext** for CSR resolution). **get_operand_info(name)** then fills **resolved_name** and **resolved_value** for GPR operands from the context.

Helper methods on InstructionInstance (**gpr_sources**, **gpr_dests**, **fpr_sources**, **fpr_dests**) return operand name → value from **operand_values** for source/destination operands; they do not require a context.

## Related topics

- **CSR context**: [CSRs](csrs.md) — **CSRContext** and **ISA.resolve_csr**.
- **Decoding and building instances**: [Decoder and encoding](decoder-and-encoding.md).
- **Data layout**: [Data and packaging](data-and-packaging.md) — where GPR/FPR YAML and schemas live.
