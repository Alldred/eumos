# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Tests for validation.load_yaml and validate_yaml_schema."""

import tempfile
from pathlib import Path

import pytest
import validation


def test_load_yaml_returns_expected_dict():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("name: foo\nlist: [a, b]\n")
        path = f.name
    try:
        data = validation.load_yaml(path)
        assert data["name"] == "foo"
        assert data["list"] == ["a", "b"]
    finally:
        Path(path).unlink(missing_ok=True)


def test_validate_yaml_schema_valid_instruction_does_not_raise():
    repo_root = Path(__file__).resolve().parent.parent
    instr_path = repo_root / "yaml" / "rv64" / "instructions" / "I" / "ADDI.yml"
    schema_path = repo_root / "yaml" / "schemas" / "instruction_schema.yaml"
    validation.validate_yaml_schema(str(instr_path), str(schema_path))


def test_validate_yaml_schema_valid_format_does_not_raise():
    repo_root = Path(__file__).resolve().parent.parent
    format_path = repo_root / "yaml" / "rv64" / "formats" / "I.yml"
    schema_path = repo_root / "yaml" / "schemas" / "format_schema.yaml"
    validation.validate_yaml_schema(str(format_path), str(schema_path))


def test_validate_yaml_schema_invalid_raises():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("mnemonic: addi\n")  # missing required name, format, extension
        path = f.name
    repo_root = Path(__file__).resolve().parent.parent
    schema_path = repo_root / "yaml" / "schemas" / "instruction_schema.yaml"
    try:
        with pytest.raises(Exception):
            validation.validate_yaml_schema(path, str(schema_path))
    finally:
        Path(path).unlink(missing_ok=True)
