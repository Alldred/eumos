# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Tests for instruction_loader.load_instruction and load_all_instructions."""

from pathlib import Path

import instruction_loader
import models


def _paths():
    repo = Path(__file__).resolve().parent.parent
    return {
        "format_dir": repo / "yaml" / "rv64" / "formats",
        "instr_root": repo / "yaml" / "rv64" / "instructions",
        "addi_yml": repo / "yaml" / "rv64" / "instructions" / "I" / "ADDI.yml",
        "sd_yml": repo / "yaml" / "rv64" / "instructions" / "I" / "SD.yml",
        "ecall_yml": repo / "yaml" / "rv64" / "instructions" / "I" / "ECALL.yml",
    }


def test_load_instruction_addi():
    p = _paths()
    instr = instruction_loader.load_instruction(
        str(p["addi_yml"]), str(p["format_dir"])
    )
    assert isinstance(instr, models.InstructionDef)
    assert instr.mnemonic == "addi"
    assert instr.extension == "I"
    assert instr.format.name == "I"
    assert instr.inputs == ["rd", "rs1", "imm"]
    assert instr.fixed_values.get("opcode") == 0x13
    assert instr.fixed_values.get("funct3") == 0x0
    assert (
        "rd" in instr.operands and "rs1" in instr.operands and "imm" in instr.operands
    )
    assert instr.operands["rd"].type == "register"
    assert instr.operands["imm"].type == "immediate"


def test_load_instruction_sd_has_split_imm():
    p = _paths()
    instr = instruction_loader.load_instruction(str(p["sd_yml"]), str(p["format_dir"]))
    assert instr.format.name == "S"
    assert "imm" in instr.fields
    assert instr.fields["imm"].parts is not None
    assert len(instr.fields["imm"].parts) >= 1


def test_load_instruction_ecall():
    p = _paths()
    instr = instruction_loader.load_instruction(
        str(p["ecall_yml"]), str(p["format_dir"])
    )
    assert instr.imm == 0x0
    assert instr.inputs == []
    assert instr.extension == "I"


def test_load_all_instructions_returns_dict():
    p = _paths()
    instrs = instruction_loader.load_all_instructions(
        str(p["instr_root"]), str(p["format_dir"])
    )
    assert isinstance(instrs, dict)
    assert len(instrs) == 60
    assert "addi" in instrs
    assert "sd" in instrs
    assert "beq" in instrs
    addi = instrs["addi"]
    assert addi.name == "ADDI"
    assert addi.mnemonic == "addi"
    assert addi.extension == "I"
