# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Tests for decoder.Decoder."""

from eumos import instruction_loader
from eumos.decoder import Decoder
from eumos.instance import InstructionInstance, RegisterContext


def _decoder():
    instructions = instruction_loader.load_all_instructions()
    return Decoder(instructions=instructions)


def test_decode_addi_returns_instruction_instance():
    """Decoding a valid ADDI word returns InstructionInstance with instruction and operand_values."""
    dec = _decoder()
    # addi x1, x2, 4  -> rd=1, rs1=2, imm=4, opcode=0x13, funct3=0
    word = 0x13 | (1 << 7) | (0 << 12) | (2 << 15) | (4 << 20)
    instance = dec.from_opc(word)
    assert instance is not None
    assert isinstance(instance, InstructionInstance)
    assert instance.instruction.mnemonic == "addi"
    assert instance.instruction.name == "ADDI"
    assert instance.operand_values["rd"] == 1
    assert instance.operand_values["rs1"] == 2
    assert instance.operand_values["imm"] == 4


def test_decode_addi_negative_immediate_sign_extended():
    """I-type immediate is sign-extended (e.g. -1 from 0xfff)."""
    dec = _decoder()
    # addi x0, x0, -1  -> imm 0xfff (12-bit -1)
    word = 0x13 | (0 << 7) | (0 << 12) | (0 << 15) | (0xFFF << 20)
    instance = dec.from_opc(word)
    assert instance is not None
    assert instance.operand_values["imm"] == -1


def test_decode_sll_r_type():
    """R-type SLL decodes with rd, rs1, rs2 and funct7 in lookup."""
    dec = _decoder()
    # sll x3, x4, x5  -> rd=3, rs1=4, rs2=5, opcode=0x33, funct3=1, funct7=0
    word = 0x33 | (3 << 7) | (1 << 12) | (4 << 15) | (5 << 20) | (0 << 25)
    instance = dec.from_opc(word)
    assert instance is not None
    assert instance.instruction.mnemonic == "sll"
    assert instance.operand_values["rd"] == 3
    assert instance.operand_values["rs1"] == 4
    assert instance.operand_values["rs2"] == 5


def test_decode_sd_s_type_split_imm():
    """S-type SD decodes with split immediate."""
    dec = _decoder()
    # sd rs2=6, imm=8, rs1=7 -> opcode=0x23, funct3=3
    # imm: [31:25]=0, [11:7]=8 (low 5 bits of 8)
    word = 0x23 | (7 << 15) | (3 << 12) | (6 << 20) | (8 << 7)
    instance = dec.from_opc(word)
    assert instance is not None
    assert instance.instruction.mnemonic == "sd"
    assert instance.operand_values["rs1"] == 7
    assert instance.operand_values["rs2"] == 6
    assert instance.operand_values["imm"] == 8


def test_decode_unknown_returns_none():
    """Unknown opcode returns None."""
    dec = _decoder()
    word = 0xFFFFFFFF  # invalid / unimplemented
    instance = dec.from_opc(word)
    assert instance is None


def test_from_opc_with_custom_instructions():
    """Decoder.from_opc() works with custom instructions dict."""
    instructions = instruction_loader.load_all_instructions()
    dec = Decoder(instructions=instructions)
    word = 0x13 | (1 << 7) | (0 << 12) | (2 << 15) | (4 << 20)
    instance = dec.from_opc(word)
    assert instance is not None
    assert instance.instruction.mnemonic == "addi"


def test_from_opc_accepts_pc_and_register_context():
    """Decoder.from_opc() accepts optional pc and register_context."""
    dec = _decoder()
    word = 0x13 | (0 << 7) | (0 << 12) | (0 << 15) | (0 << 20)
    instance = dec.from_opc(word, pc=0x1000)
    assert instance is not None
    assert instance.pc == 0x1000
    # register_context can be passed; without it resolved_* stay None
    assert instance.register_context is None


def test_register_decoder():
    """Decoding with RegisterContext populates resolved_name and resolved_value for register operands."""
    dec = _decoder()
    # addi x1, x2, 4  -> rd=1, rs1=2
    word = 0x13 | (1 << 7) | (0 << 12) | (2 << 15) | (4 << 20)
    regs = RegisterContext()
    regs.set(1, name="ra", value=0x1000)
    regs.set(2, name="sp", value=0x8000)
    instance = dec.from_opc(word, register_context=regs)
    assert instance is not None
    assert instance.register_context is regs
    rd_info = instance.get_operand_info("rd")
    rs1_info = instance.get_operand_info("rs1")
    assert rd_info is not None and rd_info.value == 1
    assert rd_info.resolved_name == "ra"
    assert rd_info.resolved_value == 0x1000
    assert rs1_info is not None and rs1_info.value == 2
    assert rs1_info.resolved_name == "sp"
    assert rs1_info.resolved_value == 0x8000
