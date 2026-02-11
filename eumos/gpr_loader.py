# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Load RISC-V GPR YAML into Python objects."""

import os
from typing import Dict

from .models import GPRDef
from .validation import load_yaml, validate_yaml_schema


def load_all_gprs() -> Dict[int, GPRDef]:
    """Load all GPR YAML files from built-in arch/rv64/gprs; returns dict index -> GPRDef."""
    gpr_root = os.path.join(os.path.dirname(__file__), "arch", "rv64", "gprs")
    gpr_root = os.path.abspath(gpr_root)
    schema_path = os.path.join(
        os.path.dirname(__file__), "arch", "schemas", "gpr_file_schema.yaml"
    )
    result: Dict[int, GPRDef] = {}
    for file in os.listdir(gpr_root):
        if file.endswith(".yml") or file.endswith(".yaml"):
            file_path = os.path.join(gpr_root, file)
            validate_yaml_schema(file_path, schema_path)
            data = load_yaml(file_path)
            result[data["index"]] = GPRDef(**data)
    return result
