# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Load RISC-V FPR YAML into Python objects."""

import os
from typing import Dict

from .models import FPRDef
from .validation import load_yaml, validate_yaml_schema


def load_all_fprs() -> Dict[int, FPRDef]:
    """Load all FPR YAML files from built-in arch/rv64/fprs; returns dict index -> FPRDef."""
    fpr_root = os.path.join(os.path.dirname(__file__), "arch", "rv64", "fprs")
    fpr_root = os.path.abspath(fpr_root)
    schema_path = os.path.join(
        os.path.dirname(__file__), "arch", "schemas", "fpr_file_schema.yaml"
    )
    result: Dict[int, FPRDef] = {}
    for file in os.listdir(fpr_root):
        if file.endswith(".yml") or file.endswith(".yaml"):
            file_path = os.path.join(fpr_root, file)
            validate_yaml_schema(file_path, schema_path)
            data = load_yaml(file_path)
            result[data["index"]] = FPRDef(**data)
    return result
