# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Load RISC-V instruction and format YAML into Python objects.

Loads specification YAML (instruction_schema, format_schema) and builds
InstructionDef, FormatDef, Operand, and related types. Run as a script
to print a sample instruction: python3 python/instruction_loader.py
"""

import os
import sys

# So that running python3 python/instruction_loader.py from repo root finds sibling modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from format_loader import load_format
from models import (
    FieldEncoding,
    InstructionDef,
    Operand,
)
from validation import load_yaml, validate_yaml_schema


def _project_root():
    """Project root (parent of python/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_instruction(instr_path, format_dir):
    """Load and validate one instruction YAML; resolves format from format_dir; returns InstructionDef."""
    schema_path = os.path.join(
        _project_root(), "arch", "schemas", "instruction_schema.yaml"
    )
    validate_yaml_schema(instr_path, schema_path)
    data = load_yaml(instr_path)
    fmt = load_format(format_dir, data["format"])
    fixed_keys = ["opcode", "funct3", "funct7"]
    fixed_values = {}
    if "fixed_values" in data:
        fixed_values = {
            k: data["fixed_values"][k] for k in fixed_keys if k in data["fixed_values"]
        }
    operands = {}
    fields = {}
    for field in fmt.fields:
        if hasattr(field, "parts") and field.parts:
            total_bits = 0
            for part in field.parts:
                bits = part.bits
                if len(bits) == 2:
                    msb, lsb = bits
                    total_bits += abs(msb - lsb) + 1
                else:
                    total_bits += 1
            operands[field.name] = Operand(
                name=field.name,
                type=field.type,
                size=total_bits,
                data=fixed_values.get(field.name),
            )
            fields[field.name] = FieldEncoding(
                name=field.name, type=field.type, parts=field.parts
            )
        else:
            bits = field.bits
            if len(bits) == 2:
                msb, lsb = bits
                size = abs(msb - lsb) + 1
            else:
                size = 1
            data_val = fixed_values.get(field.name)
            operands[field.name] = Operand(
                name=field.name, type=field.type, size=size, data=data_val
            )
            fields[field.name] = FieldEncoding(
                name=field.name, type=field.type, bits=field.bits
            )
    return InstructionDef(
        name=data["name"],
        mnemonic=data["mnemonic"],
        fixed_values=fixed_values,
        imm=data.get("imm"),
        format=fmt,
        description=data.get("description", ""),
        inputs=data.get("inputs", []),
        operands=operands,
        fields=fields,
        extension=data.get("extension", ""),
        source_file=instr_path,
    )


def load_all_instructions(
    instr_root=None,
    format_dir=None,
):
    """Walk instr_root for .yml/.yaml instruction files and load each; returns dict mnemonic -> InstructionDef."""
    if instr_root is None:
        instr_root = "arch/rv64/instructions"
    if format_dir is None:
        format_dir = "arch/rv64/formats"
    instructions = {}
    for root, _, files in os.walk(instr_root):
        for file in files:
            if file.endswith(".yml") or file.endswith(".yaml"):
                instr_path = os.path.join(root, file)
                instr = load_instruction(instr_path, format_dir)
                instructions[instr.mnemonic] = instr
    return instructions


if __name__ == "__main__":
    instrs = load_all_instructions()
    if instrs:
        first_instr = instrs["sd"]
        for k, v in first_instr.__dict__.items():
            if isinstance(v, dict):
                print(f"{k}:")
                for key, item in v.items():
                    print(f"  {key}: {item}")
            else:
                print(f"{k}: {v}")
    else:
        print("No instructions found.")
