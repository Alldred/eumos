# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Tests for instruction_loader.load_all_instructions."""

from eumos import instruction_loader, models


def test_load_instruction_addi():
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["addi"]
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
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["sd"]
    assert instr.format.name == "S"
    assert "imm" in instr.fields
    assert instr.fields["imm"].parts is not None
    assert len(instr.fields["imm"].parts) >= 1


def test_load_instruction_ecall():
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["ecall"]
    assert instr.imm == 0x0
    assert instr.inputs == []
    assert instr.extension == "I"


def test_load_all_instructions_returns_dict():
    instrs = instruction_loader.load_all_instructions()
    assert isinstance(instrs, dict)
    assert len(instrs) == 60
    assert "addi" in instrs
    assert "sd" in instrs
    assert "beq" in instrs
    addi = instrs["addi"]
    assert addi.name == "ADDI"
    assert addi.mnemonic == "addi"
    assert addi.extension == "I"
