# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Load RISC-V CSR YAML into Python objects."""

import os
from typing import Dict

from .models import CSR, CSRFieldDef
from .validation import load_yaml, validate_yaml_schema

_CSR_SCHEMA = os.path.join(
    os.path.dirname(__file__), "arch", "schemas", "csr_schema.yaml"
)
_CSR_ROOT = os.path.join(os.path.dirname(__file__), "arch", "rv64", "csrs")


def _load_csr(file_path: str, schema_path: str) -> CSR:
    """Load and validate a single CSR YAML file. Expects exactly one CSR per file."""
    validate_yaml_schema(file_path, schema_path)
    data = load_yaml(file_path)
    csrs = data.get("csrs", [data])
    if len(csrs) != 1:
        raise ValueError(f"Expected exactly one CSR in {file_path}, found {len(csrs)}.")
    raw = csrs[0]
    if "fields" in raw and isinstance(raw["fields"], list):
        raw = dict(raw)

        def _csr_field_def(f):
            f = dict(f)
            bits = f.get("bits")
            if isinstance(bits, list):
                f["bits"] = tuple(bits)
            return CSRFieldDef(**f)

        raw["fields"] = {f["name"]: _csr_field_def(f) for f in raw["fields"]}
    return CSR(**raw)


def load_all_csrs() -> Dict[str, CSR]:
    """Load all CSR YAML files from built-in arch/rv64/csrs; returns dict name -> CSR."""
    csr_root = os.path.abspath(_CSR_ROOT)
    schema_path = _CSR_SCHEMA
    result: Dict[str, CSR] = {}
    for file in os.listdir(csr_root):
        if file.endswith(".yml") or file.endswith(".yaml"):
            file_path = os.path.join(csr_root, file)
            csr_obj = _load_csr(file_path, schema_path)
            result[csr_obj.name] = csr_obj
    return result
