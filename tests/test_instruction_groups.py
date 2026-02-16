# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Tests for instruction groups: loader validation, in_group, filter APIs, smoke."""

import pytest

from eumos import instruction_groups, instruction_loader, instructions_by_group, models


def test_loader_rejects_empty_groups(tmp_path):
    """Loader must reject instruction YAML with empty groups list."""
    bad_yml = tmp_path / "bad.yml"
    bad_yml.write_text("""
name: BAD
mnemonic: bad
format: I
asm_format: default
fixed_values:
  opcode: 0x13
  funct3: 0x0
inputs:
  - rd
  - rs1
  - imm
extension: "I"
groups: []
description: bad
""")
    formats = instruction_loader.load_all_formats()
    schema = instruction_loader._INSTR_SCHEMA
    with pytest.raises(ValueError, match="non-empty"):
        instruction_loader._load_instruction(str(bad_yml), schema, formats)


def test_loader_rejects_missing_groups(tmp_path):
    """Loader must reject instruction YAML with missing groups (schema rejects required key)."""
    bad_yml = tmp_path / "bad.yml"
    bad_yml.write_text("""
name: BAD
mnemonic: bad
format: I
asm_format: default
fixed_values:
  opcode: 0x13
  funct3: 0x0
inputs:
  - rd
  - rs1
  - imm
extension: "I"
description: bad
""")
    formats = instruction_loader.load_all_formats()
    schema = instruction_loader._INSTR_SCHEMA
    with pytest.raises(Exception):  # pykwalify.SchemaError for missing required key
        instruction_loader._load_instruction(str(bad_yml), schema, formats)


def test_in_group_exact_match():
    instrs = instruction_loader.load_all_instructions()
    lw = instrs["lw"]
    assert lw.in_group("memory/load") is True
    assert lw.in_group("memory") is True


def test_in_group_prefix_match():
    instrs = instruction_loader.load_all_instructions()
    beq = instrs["beq"]
    assert beq.in_group("branch") is True
    assert beq.in_group("branch/conditional") is True


def test_in_group_no_match():
    instrs = instruction_loader.load_all_instructions()
    lw = instrs["lw"]
    assert lw.in_group("branch") is False
    assert lw.in_group("alu") is False


def test_instructions_by_group_returns_subset():
    instrs = instruction_loader.load_all_instructions()
    memory = instructions_by_group(instrs, "memory")
    assert len(memory) == 11  # 7 loads + 4 stores
    assert "lw" in memory
    assert "sd" in memory
    load_only = instructions_by_group(instrs, "memory/load")
    assert len(load_only) == 7
    assert "lw" in load_only
    assert "sd" not in load_only


def test_instruction_groups_returns_all_distinct():
    instrs = instruction_loader.load_all_instructions()
    groups = instruction_groups(instrs)
    assert isinstance(groups, list)
    assert groups == sorted(groups)
    assert "memory/load" in groups
    assert "memory/store" in groups
    assert "branch/conditional" in groups
    assert "alu" in groups


def test_all_instructions_load_with_valid_groups():
    """Smoke: all built-in instruction YAMLs load and have non-empty groups."""
    instrs = instruction_loader.load_all_instructions()
    assert len(instrs) == 60
    for mnemonic, instr in instrs.items():
        assert isinstance(instr, models.InstructionDef), mnemonic
        assert hasattr(instr, "groups"), mnemonic
        assert len(instr.groups) >= 1, f"{mnemonic} has no groups"


def test_eumos_instructions_by_group():
    from eumos import Eumos

    eu = Eumos()
    memory = eu.instructions_by_group("memory")
    assert len(memory) == 11
    assert "lw" in memory


def test_eumos_instruction_groups():
    from eumos import Eumos

    eu = Eumos()
    groups = eu.instruction_groups()
    assert isinstance(groups, list)
    assert "memory/load" in groups
    assert groups == sorted(groups)
