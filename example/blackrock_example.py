# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

# Example usage of Blackrock class

from blackrock.blackrock import Blackrock

# Instantiate Blackrock (requires $BLACKROCK_ROOT to be set in the environment)
br = Blackrock()

# Access and print summary for CSRs
gpr_names = br.gprs.keys() if hasattr(br.gprs, "keys") else br.gprs
print(f"Loaded GPRs: {gpr_names}")
print(f"Loaded {len(br.csrs)} CSRs.")
for csr_name, csr in br.csrs.items():
    print(f"CSR: {csr_name}, address: {csr.address}, privilege: {csr.privilege}")
    break  # Show only the first CSR for brevity

# Access and print summary for formats
print(f"Loaded {len(br.formats)} instruction formats.")
for fmt_name, fmt in br.formats.items():
    print(f"Format: {fmt_name}, asm_format: {getattr(fmt, 'asm_format', None)}")
    break  # Show only the first format for brevity

# Access and print summary for instructions
print(f"Loaded {len(br.instructions)} instructions.")
for name, details in br.instructions.items():
    print(f"Instruction: {name}")
    print("  Description:", details.description)
    print(
        "  Format:",
        details.format.asm_format
        if hasattr(details.format, "asm_format")
        else details.format,
    )
    print("  Operands:")
    for op_name, op in details.operands.items():
        print(f"    {op_name}: type={op.type}, size={op.size}, data={op.data}")
    print("  Fields:")
    for field_name, field in details.fields.items():
        print(
            f"    {field_name}: type={field.type}, bits={getattr(field, 'bits', None)}, parts={getattr(field, 'parts', None)}"
        )
    print("  Extension:", details.extension)
    print("  Source file:", details.source_file)
    break  # Show only the first instruction for brevity
