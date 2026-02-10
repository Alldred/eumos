# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Load RISC-V format YAML into Python objects."""

import os
from typing import Dict

from models import Format
from validation import load_yaml, validate_yaml_schema


def load_format(file_path: str, schema_path: str) -> Format:
    """Load and validate a single format YAML file."""
    validate_yaml_schema(file_path, schema_path)
    data = load_yaml(file_path)
    for fmt in data["formats"]:
        return Format(**fmt)
    raise ValueError(f"No format found in {file_path}")


def load_all_formats() -> Dict[str, Format]:
    """Load all format YAML files in arch/rv64/formats; returns dict name -> Format."""
    format_root = os.path.join(os.path.dirname(__file__), "arch", "rv64", "formats")
    format_root = os.path.abspath(format_root)
    schema_path = os.path.join(
        os.path.dirname(__file__), "arch", "schemas", "format_file_schema.yaml"
    )
    result: Dict[str, Format] = {}
    for file in os.listdir(format_root):
        if file.endswith(".yml") or file.endswith(".yaml"):
            file_path = os.path.join(format_root, file)
            fmt_obj = load_format(file_path, schema_path)
            result[fmt_obj.name] = fmt_obj
    return result
