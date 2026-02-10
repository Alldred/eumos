# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Load RISC-V CSR YAML into Python objects."""

import os
from typing import Dict

from models import CSR
from validation import load_yaml, validate_yaml_schema


def load_csr(file_path: str, schema_path: str) -> CSR:
    """Load and validate a single CSR YAML file."""
    validate_yaml_schema(file_path, schema_path)
    data = load_yaml(file_path)
    for csr in data["csrs"]:
        return CSR(**csr)
    raise ValueError(f"No CSR found in {file_path}")


def load_all_csrs() -> Dict[str, CSR]:
    """Load all CSR YAML files in arch/rv64/csrs; returns dict name -> CSR."""
    csr_root = os.path.join(os.path.dirname(__file__), "arch", "rv64", "csrs")
    csr_root = os.path.abspath(csr_root)
    schema_path = os.path.join(
        os.path.dirname(__file__), "arch", "schemas", "csr_file_schema.yaml"
    )
    result: Dict[str, CSR] = {}
    for file in os.listdir(csr_root):
        if file.endswith(".yml") or file.endswith(".yaml"):
            file_path = os.path.join(csr_root, file)
            csr_obj = load_csr(file_path, schema_path)
            result[csr_obj.name] = csr_obj
    return result
