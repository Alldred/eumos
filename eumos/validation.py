# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""YAML loading and schema validation (pykwalify)."""

import yaml
from pykwalify.core import Core


def validate_yaml_schema(yaml_path, schema_path):
    """Validate a YAML file against a pykwalify schema; raises on failure."""
    core = Core(source_file=yaml_path, schema_files=[schema_path])
    core.validate()


def load_yaml(filepath):
    """Load and return the contents of a YAML file as a dict."""
    with open(filepath, "r") as f:
        return yaml.safe_load(f)
