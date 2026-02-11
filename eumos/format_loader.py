# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Load RISC-V format YAML into Python objects."""

import os
from typing import Dict

from .models import FieldDef, FieldPart, Format
from .validation import load_yaml, validate_yaml_schema

_FORMAT_SCHEMA = os.path.join(
    os.path.dirname(__file__), "arch", "schemas", "format_schema.yaml"
)
_FORMAT_ROOT = os.path.join(os.path.dirname(__file__), "arch", "rv64", "formats")


def _load_format(file_path: str, schema_path: str) -> Format:
    """Load and validate a single format YAML file. Expects exactly one format per file."""
    validate_yaml_schema(file_path, schema_path)
    data = load_yaml(file_path)
    formats = data.get("formats", [data])
    if len(formats) != 1:
        raise ValueError(
            f"Expected exactly one format in {file_path}, found {len(formats)}."
        )
    raw = formats[0]
    if "fields" in raw and isinstance(raw["fields"], list):
        raw = dict(raw)

        def _field_def_from_raw(f):
            f = dict(f)
            if "parts" in f and f["parts"]:
                f["parts"] = [FieldPart(**p) for p in f["parts"]]
            return FieldDef(**f)

        raw["fields"] = [_field_def_from_raw(f) for f in raw["fields"]]
    return Format(**raw)


def load_all_formats() -> Dict[str, Format]:
    """Load all format YAML files from built-in arch/rv64/formats; returns dict name -> Format."""
    format_root = os.path.abspath(_FORMAT_ROOT)
    schema_path = _FORMAT_SCHEMA
    result: Dict[str, Format] = {}
    for file in os.listdir(format_root):
        if file.endswith(".yml") or file.endswith(".yaml"):
            file_path = os.path.join(format_root, file)
            fmt_obj = _load_format(file_path, schema_path)
            result[fmt_obj.name] = fmt_obj
    return result
