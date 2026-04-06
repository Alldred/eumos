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


def test_load_instruction_slli_has_immediate_aliases():
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["slli"]
    assert instr.operand_aliases == {"imm": ["shamt"]}
    assert instr.operand_alias_lookup == {"shamt": "imm"}
    assert instr.immediate_encoding == {
        "imm": {"mode": "shift", "width": 6, "prefix": 0}
    }


def test_load_instruction_ecall():
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["ecall"]
    assert instr.imm == 0x0
    assert instr.inputs == []
    assert instr.extension == "I"


def test_load_instruction_mul_extension():
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["mul"]
    assert instr.mnemonic == "mul"
    assert instr.extension == "M"
    assert instr.format.name == "R"
    assert instr.fixed_values.get("opcode") == 0x33
    assert instr.fixed_values.get("funct7") == 0x01


def test_load_instruction_div_behavior_metadata():
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["div"]
    assert instr.extension == "M"
    assert instr.behavior == {
        "arithmetic": {
            "operation": "div",
            "result": "quotient",
            "width": "xlen",
            "signed_operands": True,
            "rounding": "toward_zero",
            "divide_by_zero": "all_ones",
            "overflow": {
                "case": "int_min_div_neg_one",
                "result": "dividend",
            },
        }
    }


def test_load_instruction_csrrw_is_zicsr():
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["csrrw"]
    assert instr.extension == "Zicsr"


def test_load_instruction_czero_eqz():
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["czero.eqz"]
    assert isinstance(instr, models.InstructionDef)
    assert instr.mnemonic == "czero.eqz"
    assert instr.extension == "Zicond"
    assert instr.format.name == "R"
    assert instr.inputs == ["rd", "rs1", "rs2"]
    assert instr.fixed_values.get("opcode") == 0x33
    assert instr.fixed_values.get("funct3") == 0x5
    assert instr.fixed_values.get("funct7") == 0x07


def test_load_all_instructions_returns_dict():
    instrs = instruction_loader.load_all_instructions()
    assert isinstance(instrs, dict)
    assert len(instrs) == 137
    assert "addi" in instrs
    assert "sd" in instrs
    assert "beq" in instrs
    assert "mul" in instrs
    assert "mulw" in instrs
    assert "czero.eqz" in instrs
    assert "czero.nez" in instrs
    addi = instrs["addi"]
    assert addi.name == "ADDI"
    assert addi.mnemonic == "addi"
    assert addi.extension == "I"
