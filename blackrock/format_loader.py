# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Load format YAML (R, I, S, B, etc.) into FormatDef."""

import importlib.resources
import os
from typing import Dict, Optional

from models import FieldDef, FieldPart, FormatDef
from validation import load_yaml, validate_yaml_schema


def _project_root():
    """Return the package root for importlib.resources."""
    return importlib.resources.files("blackrock")


def load_format(format_dir, format_name):
    """Load and validate one format (e.g. I, R, S, B) from format_dir; returns FormatDef."""
    path = os.path.join(format_dir, format_name + ".yml")
    schema_path = os.path.join(
        os.path.dirname(__file__), "arch", "schemas", "format_schema.yaml"
    )
    schema_path = os.path.abspath(schema_path)
    validate_yaml_schema(path, schema_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Format file not found: {path}")
    data = load_yaml(path)
    fields = []
    for fld in data.get("fields", []):
        if "parts" in fld:
            parts = [
                FieldPart(bits=p["bits"], operand_bits=p.get("operand_bits"))
                for p in fld["parts"]
            ]
            fields.append(FieldDef(name=fld["name"], type=fld["type"], parts=parts))
        else:
            fields.append(FieldDef(**fld))
    return FormatDef(
        name=data["name"],
        fullname=data.get("fullname", ""),
        asm_format=data.get("asm_format", ""),
        fields=fields,
        description=data.get("description", ""),
    )


def load_all_formats(format_root: Optional[str] = None) -> Dict[str, FormatDef]:
    """Load all format YAML files in format_root; returns dict name -> FormatDef."""
    if format_root is None:
        format_root = os.path.join(os.path.dirname(__file__), "arch", "rv64", "formats")
        format_root = os.path.abspath(format_root)
    schema_path = os.path.join(
        os.path.dirname(__file__), "arch", "schemas", "format_schema.yaml"
    )
    schema_path = os.path.abspath(schema_path)
    result: Dict[str, FormatDef] = {}
    for file in os.listdir(format_root):
        if file.endswith(".yml") or file.endswith(".yaml"):
            name = os.path.splitext(file)[0]
            path = os.path.join(format_root, file)
            validate_yaml_schema(path, schema_path)
            result[name] = load_format(format_root, name)
    return result
