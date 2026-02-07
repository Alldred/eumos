# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Load RISC-V CSR YAML into Python objects."""

import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import CSRDef, CSRFieldDef
from validation import load_yaml, validate_yaml_schema


def _project_root():
    """Project root (parent of python/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _normalize_bits(bits: Any) -> Union[int, Tuple[int, int]]:
    """Normalize bits to int (single bit) or (high, low) inclusive tuple."""
    if isinstance(bits, int):
        return bits
    if isinstance(bits, (list, tuple)) and len(bits) == 2:
        hi, lo = int(bits[0]), int(bits[1])
        if hi < lo:
            hi, lo = lo, hi
        return (hi, lo)
    raise ValueError(f"bits must be int or [high, low], got {bits!r}")


def _parse_fields(raw_fields: Optional[List[Any]]) -> Optional[Dict[str, CSRFieldDef]]:
    """Parse YAML fields list into name -> CSRFieldDef."""
    if not raw_fields:
        return None
    result: Dict[str, CSRFieldDef] = {}
    for entry in raw_fields:
        name = entry["name"]
        bits = _normalize_bits(entry["bits"])
        result[name] = CSRFieldDef(
            name=name,
            bits=bits,
            description=entry.get("description", ""),
            reset_value=entry.get("reset_value"),
            access=entry.get("access"),
        )
    return result


def load_csr(csr_path: str, schema_path: Optional[str] = None) -> CSRDef:
    """Load and validate one CSR YAML; returns CSRDef."""
    if schema_path is None:
        schema_path = os.path.join(
            _project_root(), "arch", "schemas", "csr_schema.yaml"
        )
    validate_yaml_schema(csr_path, schema_path)
    data = load_yaml(csr_path)
    address = data["address"]
    if not (0 <= address <= 0xFFF):
        raise ValueError(f"CSR address must be 12-bit (0x000-0xFFF), got {address}")
    fields = _parse_fields(data.get("fields"))
    return CSRDef(
        name=data["name"],
        address=address,
        description=data.get("description", ""),
        privilege=data.get("privilege"),
        access=data.get("access"),
        width=data.get("width"),
        extension=data.get("extension"),
        reset_value=data.get("reset_value"),
        fields=fields,
        source_file=csr_path,
    )


def load_all_csrs(csr_root: Optional[str] = None) -> dict:
    """Walk csr_root for .yml/.yaml CSR files and load each; returns dict name -> CSRDef."""
    if csr_root is None:
        csr_root = os.path.join(_project_root(), "arch", "rv64", "csrs")
    csrs = {}
    for root, _, files in os.walk(csr_root):
        for file in files:
            if file.endswith(".yml") or file.endswith(".yaml"):
                csr_path = os.path.join(root, file)
                csr = load_csr(csr_path)
                csrs[csr.name] = csr
    return csrs
