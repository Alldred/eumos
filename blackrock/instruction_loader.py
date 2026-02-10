# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Load RISC-V instruction and format YAML into Python objects.

Loads specification YAML (instruction_schema, format_schema) and builds
InstructionDef, FormatDef, Operand, and related types. Run as a script
to print a sample instruction: python3 python/instruction_loader.py
"""

import importlib.resources
import os
import sys
from typing import Dict, Optional

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
    """Return the package root for importlib.resources."""
    return importlib.resources.files("blackrock")


def load_instruction(instr_path, format_dir):
    """Load and validate one instruction YAML; resolves format from format_dir; returns InstructionDef."""
    schema_path = os.path.join(
        _project_root(), "arch", "schemas", "instruction_schema.yaml"
    )
    validate_yaml_schema(instr_path, schema_path)
    data = load_yaml(instr_path)
    fmt = load_format(format_dir, data["format"])
    fixed_keys = ["opcode", "funct3", "funct7"]
    fixed_values = {
        k: data["fixed_values"][k]
        for k in fixed_keys
        if "fixed_values" in data and k in data["fixed_values"]
    }

    operands = {}
    fields = {}
    for field in fmt.fields:
        size = 1
        if hasattr(field, "parts") and field.parts:
            size = sum(
                abs(part.bits[0] - part.bits[1]) + 1 if len(part.bits) == 2 else 1
                for part in field.parts
            )
            operands[field.name] = Operand(
                name=field.name,
                type=field.type,
                size=size,
                data=fixed_values.get(field.name),
            )
            fields[field.name] = FieldEncoding(
                name=field.name, type=field.type, parts=field.parts
            )
        else:
            if len(field.bits) == 2:
                size = abs(field.bits[0] - field.bits[1]) + 1
            operands[field.name] = Operand(
                name=field.name,
                type=field.type,
                size=size,
                data=fixed_values.get(field.name),
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


# Note: InstructionDef.operands are the logical inputs (registers, immediates, etc.) used by the instruction.
#       InstructionDef.fields are the bit-level encoding details for those operands and other instruction components.
#       Operands represent what the instruction uses semantically; fields represent how those values are encoded in the instruction word.


def load_all_instructions(
    instr_root: Optional[str] = None, format_dir: Optional[str] = None
) -> Dict[str, InstructionDef]:
    """Load all instruction YAML files in instr_root; returns dict name -> InstructionDef."""
    if instr_root is None:
        instr_root = os.path.join(
            os.path.dirname(__file__), "arch", "rv64", "instructions"
        )
        instr_root = os.path.abspath(instr_root)
    if format_dir is None:
        format_dir = os.path.join(os.path.dirname(__file__), "arch", "rv64", "formats")
        format_dir = os.path.abspath(format_dir)
    result: Dict[str, InstructionDef] = {}
    for root, dirs, files in os.walk(instr_root):
        for file in files:
            if file.endswith(".yml") or file.endswith(".yaml"):
                name = os.path.splitext(file)[0]
                file_path = os.path.join(root, file)
                result[name] = load_instruction(file_path, format_dir)
    return result
