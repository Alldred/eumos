# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

# Example usage of Eumos class

from eumos import Eumos

# Instantiate Eumos (requires $EUMOS_ROOT to be set in the environment)
eu = Eumos()

print("\n=== Eumos Example Output ===\n")

# Access and print summary for GPRs
print(f"Loaded {len(eu.gprs)} GPRs.")
example_gpr_idx, example_gpr = next(iter(eu.gprs.items()))
print(
    f"Example GPR:\n  x{example_gpr_idx} ({example_gpr.abi_name})\n  reset_value: {example_gpr.reset_value}\n  access: {example_gpr.access}\n"
)

print(f"Loaded {len(eu.csrs)} CSRs.")
for csr_name, csr in sorted(eu.csrs.items()):
    print(
        f"Example CSR:\n  {csr_name}\n  address: {csr.address}\n  privilege: {csr.privilege}\n"
    )
    break  # Show only the first CSR for brevity

print(f"Loaded {len(eu.formats)} instruction formats.")
for fmt_name, fmt in sorted(eu.formats.items()):
    print(
        f"Example Format:\n  {fmt_name}\n  asm_format: {getattr(fmt, 'asm_format', None)}\n"
    )
    break  # Show only the first format for brevity

print(f"Loaded {len(eu.instructions)} instructions.")
for name, details in sorted(eu.instructions.items()):
    print(f"Example Instruction:\n  {name}\n  Description: {details.description}\n")
    print(
        f"  Format: {details.format.asm_format if hasattr(details.format, 'asm_format') else details.format}"
    )
    print("  Operands:")
    for op_name, op in sorted(details.operands.items()):
        print(f"    {op_name}: type={op.type}, size={op.size}, data={op.data}")
    print("  Fields:")
    for field_name, field in sorted(details.fields.items()):
        print(
            f"    {field_name}: type={field.type}, bits={getattr(field, 'bits', None)}, parts={getattr(field, 'parts', None)}"
        )
    print(f"  Extension: {details.extension}")
    print(f"  Source file: {details.source_file}\n")
    break  # Show only the first instruction for brevity
