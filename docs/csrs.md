<!--
  ~ SPDX-License-Identifier: MIT
  ~ Copyright (c) 2026 Stuart Alldred.
  -->

# CSRs

This page describes how to load and use Control and Status Register (CSR) definitions in Eumos, and how to tie them to instruction instances and runtime values.

## Loading CSRs

**From the Eumos facade:**

```python
from eumos import Eumos

eu = Eumos()
# eu.csrs: name -> CSRDef
mstatus = eu.csrs["mstatus"]
print(mstatus.address, mstatus.privilege, mstatus.description)
```

**From the CSR loader directly:**

```python
from eumos.csr_loader import load_all_csrs

csrs = load_all_csrs()
# csrs: name (e.g. "mstatus", "mepc") -> CSRDef
```

CSR YAML files are loaded from the built-in `arch/rv64/csrs/` directory and validated with `arch/schemas/csr_file_schema.yaml`. See [Data and packaging](data-and-packaging.md).

## CSRDef fields

Each **CSRDef** (also referred to as **CSR** in the loader) has:

- **name** — e.g. `"mstatus"`, `"mepc"`.
- **address** — 12-bit CSR address.
- **description** — Human-readable description.
- **privilege** — Optional; privilege level(s).
- **access** — Optional; read/write behaviour.
- **width** — Optional; width in bits.
- **extension** — Optional; extension that defines the CSR.
- **fields** — Optional; dict of named **CSRFieldDef** (bit ranges, reset value, access override).

## ISA: instructions and CSRs together

The **ISA** class (in `eumos.instance`) holds optional instructions and/or CSRs. You can load either or both:

```python
from eumos import load_all_instructions, load_all_csrs
from eumos.instance import ISA

isa = ISA(
    instructions=load_all_instructions(),
    csrs=load_all_csrs(),
)
```

When CSRs are provided, **isa.csrs_by_address** is built automatically: it maps 12-bit address → **CSRDef**, so you can resolve the `imm` operand of CSR instructions (e.g. `csrrw`, `csrrs`) to the CSR definition.

## CSRContext: runtime CSR values

**CSRContext** (in `eumos.instance`) maps CSR address (or name, if definitions are supplied) to runtime values:

```python
from eumos.instance import CSRContext

# With definitions: use names or addresses
csr_defs = load_all_csrs()
ctx = CSRContext(csr_defs=csr_defs.values())
ctx.set("mstatus", 0x1000)
value = ctx.get_value("mstatus")
addr = ctx.get_address("mstatus")
name = ctx.get_name(0x300)  # mepc
```

Without `csr_defs`, you can only use 12-bit addresses with `set` and `get_value`; `get_name` and `get_address` will not work.

## Resolving the CSR for a CSR instruction

For CSR instructions, the **imm** operand in **InstructionInstance.operand_values** is the 12-bit CSR address. To get the **CSRDef** and the current value (if you have a CSRContext), use **ISA.resolve_csr**:

```python
from eumos.instance import ISA, CSRContext

isa = ISA(instructions=load_all_instructions(), csrs=load_all_csrs())
csr_ctx = CSRContext(csr_defs=isa.csrs.values())
csr_ctx.set("mstatus", 0x1000)

# Decode a CSR instruction (e.g. csrrw a0, mstatus, zero)
# instance = decoder.from_asm("csrrw a0, mstatus, zero")
csr_def, value = isa.resolve_csr(instance, csr_ctx)
# csr_def is the CSRDef for mstatus; value is 0x1000 from context
```

If no CSRContext is passed, the second return value is None; you still get the CSRDef when the instruction’s `imm` matches a known CSR.

## Related topics

- **Instructions and decoding**: [Instructions](instructions.md), [Decoder and encoding](decoder-and-encoding.md).
- **Registers and context**: [Registers and context](registers-and-context.md).
- **Data layout**: [Data and packaging](data-and-packaging.md).
