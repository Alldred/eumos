# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Load RISC-V exception cause definitions from YAML."""

import os
from typing import Dict

from .models import ExceptionCauseDef
from .validation import load_yaml, validate_yaml_schema

_EXCEPTION_SCHEMA = os.path.join(
    os.path.dirname(__file__), "arch", "schemas", "exception_schema.yaml"
)
_EXCEPTION_FILE = os.path.join(
    os.path.dirname(__file__), "arch", "rv64", "exceptions.yml"
)


def load_all_exception_causes() -> Dict[int, ExceptionCauseDef]:
    """Load exception cause definitions from arch/rv64/exceptions.yml.

    Returns:
        Dict mapping exception code (int) to ExceptionCauseDef.
    """
    file_path = os.path.abspath(_EXCEPTION_FILE)
    schema_path = os.path.abspath(_EXCEPTION_SCHEMA)
    validate_yaml_schema(file_path, schema_path)
    data = load_yaml(file_path)
    exceptions = data.get("exceptions", [])
    return {e["code"]: ExceptionCauseDef(**e) for e in exceptions}
