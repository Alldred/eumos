# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Load RISC-V instruction YAML into Python objects, recursively."""

import os
from typing import Dict

from .models import Instruction
from .validation import load_yaml, validate_yaml_schema


def load_instruction(file_path: str, schema_path: str) -> Instruction:
    """Load and validate a single instruction YAML file. Expects exactly one instruction per file."""
    validate_yaml_schema(file_path, schema_path)
    data = load_yaml(file_path)
    instructions = data["instructions"]
    if len(instructions) != 1:
        raise ValueError(
            f"Expected exactly one instruction in {file_path}, found {len(instructions)}."
        )
    return Instruction(**instructions[0])


def load_all_instructions() -> Dict[str, Instruction]:
    """Recursively load all instruction YAML files in arch/rv64/instructions; returns dict mnemonic -> Instruction."""
    instr_root = os.path.join(os.path.dirname(__file__), "arch", "rv64", "instructions")
    instr_root = os.path.abspath(instr_root)
    schema_path = os.path.join(
        os.path.dirname(__file__), "arch", "schemas", "instruction_file_schema.yaml"
    )
    result: Dict[str, Instruction] = {}
    for dirpath, _, files in os.walk(instr_root):
        for file in files:
            if file.endswith(".yml") or file.endswith(".yaml"):
                file_path = os.path.join(dirpath, file)
                instr_obj = load_instruction(file_path, schema_path)
                result[instr_obj.mnemonic] = instr_obj
    return result
