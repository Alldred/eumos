# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Load RISC-V instruction YAML into Python objects, recursively."""

import os
from typing import Dict

from .format_loader import load_all_formats
from .models import FieldEncoding, FormatDef, Instruction, Operand
from .validation import load_yaml, validate_yaml_schema

_INSTR_SCHEMA = os.path.join(
    os.path.dirname(__file__), "arch", "schemas", "instruction_schema.yaml"
)
_INSTR_ROOT = os.path.join(os.path.dirname(__file__), "arch", "rv64", "instructions")


def _immediate_size_for_format(format_name: str) -> int:
    """Return immediate width in bits for the format."""
    if format_name in ("I", "S", "B"):
        return 12
    if format_name == "U":
        return 20
    if format_name == "J":
        return 21
    return 12


def _build_operands_and_fields(raw: dict, format_obj) -> tuple:
    """Build operands and fields dicts from format and instruction inputs."""
    inputs = raw.get("inputs") or []
    fmt_name = format_obj.name
    imm_size = _immediate_size_for_format(fmt_name)
    operands: Dict[str, Operand] = {}
    fields: Dict[str, FieldEncoding] = {}
    for f in format_obj.fields:
        name, typ = f.name, f.type
        size = 5 if typ == "register" else (imm_size if typ == "immediate" else 0)
        enc = FieldEncoding(name=name, type=typ, bits=f.bits, parts=f.parts)
        fields[name] = enc
        if name in inputs or typ in ("register", "immediate"):
            operands[name] = Operand(name=name, type=typ, size=size, data=None)
    return operands, fields


def _load_instruction(
    file_path: str, schema_path: str, formats: Dict[str, FormatDef]
) -> Instruction:
    """Load and validate a single instruction YAML file. Expects exactly one instruction per file."""
    validate_yaml_schema(file_path, schema_path)
    data = load_yaml(file_path)
    instructions = data.get("instructions", [data])
    if len(instructions) != 1:
        raise ValueError(
            f"Expected exactly one instruction in {file_path}, found {len(instructions)}."
        )
    raw = dict(instructions[0])
    format_name = raw.get("format")
    if isinstance(format_name, str) and format_name in formats:
        format_obj = formats[format_name]
        operands, fields = _build_operands_and_fields(raw, format_obj)
        raw["format"] = format_obj
        raw["operands"] = operands
        raw["fields"] = fields
        asm_format = raw.get("asm_format")
        asm_formats = getattr(format_obj, "asm_formats", None) or {}
        if asm_format not in asm_formats:
            raise ValueError(
                f"{file_path}: asm_format '{asm_format}' not in format {format_name} asm_formats {list(asm_formats)}"
            )
    # Expose fixed imm as top-level imm when present (e.g. ECALL has imm in fixed_values only)
    if "imm" not in raw and raw.get("fixed_values"):
        fv_imm = raw["fixed_values"].get("imm")
        if fv_imm is not None:
            raw["imm"] = fv_imm
    return Instruction(**raw)


def load_all_instructions() -> Dict[str, Instruction]:
    """Recursively load all instruction YAML files from built-in arch; returns dict mnemonic -> Instruction."""
    formats = load_all_formats()
    instr_root = os.path.abspath(_INSTR_ROOT)
    schema_path = _INSTR_SCHEMA
    result: Dict[str, Instruction] = {}
    for dirpath, _, files in os.walk(instr_root):
        for file in files:
            if file.endswith(".yml") or file.endswith(".yaml"):
                file_path = os.path.join(dirpath, file)
                instr_obj = _load_instruction(file_path, schema_path, formats)
                result[instr_obj.mnemonic] = instr_obj
    return result
