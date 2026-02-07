# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

# Example usage of instruction_loader.py

from slate.instruction_loader import load_all_instructions

# Adjust the path as needed for your instruction YAML files
instr_dir = "../arch/rv64/instructions/I"
format_dir = "../arch/rv64/formats"

# Load instructions
instrs = load_all_instructions(instr_root=instr_dir, format_dir=format_dir)

# Print a summary
print(f"Loaded {len(instrs)} instructions from {instr_dir}")
for name, details in instrs.items():
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
