# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Noodle-Bytes. All Rights Reserved

"""Load format YAML (R, I, S, B, etc.) into FormatDef."""

import os

from models import FieldDef, FieldPart, FormatDef
from validation import load_yaml, validate_yaml_schema


def load_format(format_dir, format_name):
    """Load and validate one format (e.g. I, R, S, B) from format_dir; returns FormatDef."""
    path = os.path.join(format_dir, format_name + ".yml")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(root, "yaml", "schemas", "format_schema.yaml")
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
