# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Load RISC-V GPR YAML into Python objects."""

import os
import sys
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import GPRDef
from validation import load_yaml, validate_yaml_schema


def _project_root():
    """Project root (parent of python/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_all_gprs(
    gpr_root: Optional[str] = None, schema_path: Optional[str] = None
) -> Dict[int, GPRDef]:
    """Load and validate all GPR YAML files in gpr_root; returns dict index -> GPRDef."""
    if gpr_root is None:
        gpr_root = os.path.join(_project_root(), "arch", "rv64", "gprs")
    if schema_path is None:
        schema_path = os.path.join(
            _project_root(), "arch", "schemas", "gpr_file_schema.yaml"
        )
    result: Dict[int, GPRDef] = {}
    for file in os.listdir(gpr_root):
        if file.endswith(".yml") or file.endswith(".yaml"):
            gpr_path = os.path.join(gpr_root, file)
            validate_yaml_schema(gpr_path, schema_path)
            data = load_yaml(gpr_path)
            idx = data["index"]
            if not (0 <= idx <= 31):
                raise ValueError(f"GPR index must be 0..31, got {idx}")
            result[idx] = GPRDef(
                index=idx,
                abi_name=data["abi_name"],
                reset_value=data["reset_value"],
                access=data["access"],
                source_file=gpr_path,
            )
    return result
