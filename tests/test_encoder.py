# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Tests for encode_instruction(): single encoding API and parity with InstructionInstance.to_opc()."""

import pytest

from eumos import instruction_loader
from eumos.decoder import Decoder
from eumos.encoder import encode_instruction


def _instance_opc(asm_str: str) -> int:
    """Parse asm to instance and return opcode (uses to_opc() which delegates to encode_instruction)."""
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)
    instance = decoder.from_asm(asm_str)
    return instance.to_opc()


def _encode_direct(mnemonic: str, operand_values: dict) -> int:
    """Encode via encode_instruction(instruction, operand_values) only."""
    instructions = instruction_loader.load_all_instructions()
    instr = instructions[mnemonic]
    return encode_instruction(instr, operand_values)


@pytest.mark.parametrize(
    "asm_str",
    [
        "addi x1, x2, 4",  # I-type
        "sll x3, x4, x5",  # R-type
        "sd x6, 8(x7)",  # S-type (split immediate)
        "beq x1, x2, 8",  # B-type (split immediate)
        "jal x1, 12",  # J-type (split immediate)
        "lui x2, 0x12345",  # U-type
        "ecall",  # zero operands
    ],
)
def test_encode_instruction_matches_to_opc(asm_str):
    """encode_instruction(instr, operand_values) matches InstructionInstance(...).to_opc()."""
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)
    instance = decoder.from_asm(asm_str)
    expected = instance.to_opc()
    actual = encode_instruction(instance.instruction, instance.operand_values)
    assert (
        actual == expected
    ), f"asm={asm_str!r} expected 0x{expected:08x} got 0x{actual:08x}"


def test_encode_instruction_r_type():
    """R-type: encode_instruction matches direct operand_values."""
    opc_instance = _instance_opc("sll x3, x4, x5")
    opc_direct = _encode_direct("sll", {"rd": 3, "rs1": 4, "rs2": 5})
    assert opc_direct == opc_instance


def test_encode_instruction_i_type():
    """I-type: encode_instruction matches direct operand_values."""
    opc_instance = _instance_opc("addi x1, x2, 4")
    opc_direct = _encode_direct("addi", {"rd": 1, "rs1": 2, "imm": 4})
    assert opc_direct == opc_instance


def test_encode_instruction_s_type():
    """S-type (split immediate): encode_instruction matches to_opc."""
    opc_instance = _instance_opc("sd x6, 8(x7)")
    opc_direct = _encode_direct("sd", {"rs1": 7, "rs2": 6, "imm": 8})
    assert opc_direct == opc_instance


def test_encode_instruction_b_type():
    """B-type (split immediate): encode_instruction matches to_opc."""
    opc_instance = _instance_opc("beq x1, x2, 8")
    opc_direct = _encode_direct("beq", {"rs1": 1, "rs2": 2, "imm": 8})
    assert opc_direct == opc_instance


def test_encode_instruction_j_type():
    """J-type (split immediate): encode_instruction matches to_opc."""
    opc_instance = _instance_opc("jal x1, 12")
    opc_direct = _encode_direct("jal", {"rd": 1, "imm": 12})
    assert opc_direct == opc_instance


def test_encode_instruction_j_type_fixed_opcode():
    """J-type fixed opcodes are encoded correctly for positive and negative offsets."""
    instructions = instruction_loader.load_all_instructions()
    instr = instructions["jal"]
    assert encode_instruction(instr, {"rd": 0, "imm": 44}) == 0x02C0006F
    assert encode_instruction(instr, {"rd": 0, "imm": -4}) == 0xFFDFF06F


def test_encode_instruction_b_type_fixed_opcode():
    """B-type fixed opcode is encoded correctly for positive and negative offsets."""
    instructions = instruction_loader.load_all_instructions()
    instr = instructions["beq"]
    assert encode_instruction(instr, {"rs1": 1, "rs2": 2, "imm": 4}) == 0x00208263
    assert encode_instruction(instr, {"rs1": 1, "rs2": 2, "imm": -4}) == 0xFE208EE3


def test_encode_instruction_b_type_boundary_offsets():
    """B-type boundary offsets encode per spec."""
    instructions = instruction_loader.load_all_instructions()
    instr = instructions["beq"]
    # Most-negative branch offset (-4096 bytes)
    assert encode_instruction(instr, {"rs1": 1, "rs2": 2, "imm": -4096}) == 0x80208063
    # Largest positive branch offset (4094 bytes)
    assert encode_instruction(instr, {"rs1": 1, "rs2": 2, "imm": 4094}) == 0x7E208FE3


def test_encode_instruction_j_type_boundary_offsets():
    """J-type boundary offsets encode per spec."""
    instructions = instruction_loader.load_all_instructions()
    instr = instructions["jal"]
    # Most-negative jump offset (-1048576 bytes)
    assert encode_instruction(instr, {"rd": 0, "imm": -1048576}) == 0x8000006F
    # Largest positive jump offset (1048574 bytes)
    assert encode_instruction(instr, {"rd": 0, "imm": 1048574}) == 0x7FFFF06F


def test_encode_instruction_shift_immediates_preserve_operation():
    """Shift-immediate opcodes include required upper immediate bits (e.g. SRAI/SRAIW)."""
    instructions = instruction_loader.load_all_instructions()
    assert (
        encode_instruction(instructions["srai"], {"rd": 1, "rs1": 2, "imm": 1})
        == 0x40115093
    )
    assert (
        encode_instruction(instructions["srai"], {"rd": 1, "rs1": 2, "imm": 63})
        == 0x43F15093
    )
    assert (
        encode_instruction(instructions["sraiw"], {"rd": 1, "rs1": 2, "imm": 1})
        == 0x4011509B
    )


def test_encode_instruction_i_type_immediate_out_of_range_raises():
    """I-type immediates outside signed 12-bit range are rejected."""
    instructions = instruction_loader.load_all_instructions()
    instr = instructions["addi"]
    with pytest.raises(ValueError, match="I-type immediate .* out of range"):
        encode_instruction(instr, {"rd": 1, "rs1": 2, "imm": 4096})
    with pytest.raises(ValueError, match="I-type immediate .* out of range"):
        encode_instruction(instr, {"rd": 1, "rs1": 2, "imm": -2049})


def test_encode_instruction_branch_jump_out_of_range_raise():
    """B/J immediates outside architectural range are rejected."""
    instructions = instruction_loader.load_all_instructions()
    beq = instructions["beq"]
    jal = instructions["jal"]
    with pytest.raises(ValueError, match="B-type immediate offset .* out of range"):
        encode_instruction(beq, {"rs1": 1, "rs2": 2, "imm": 4096})
    with pytest.raises(ValueError, match="B-type immediate offset .* out of range"):
        encode_instruction(beq, {"rs1": 1, "rs2": 2, "imm": -4098})
    with pytest.raises(ValueError, match="J-type immediate offset .* out of range"):
        encode_instruction(jal, {"rd": 1, "imm": 1048576})
    with pytest.raises(ValueError, match="J-type immediate offset .* out of range"):
        encode_instruction(jal, {"rd": 1, "imm": -1048578})


def test_encode_instruction_shift_immediate_range_raises():
    """Shift-immediate amount range is enforced per instruction."""
    instructions = instruction_loader.load_all_instructions()
    with pytest.raises(ValueError, match="SLLI shift amount .* out of range"):
        encode_instruction(instructions["slli"], {"rd": 1, "rs1": 2, "imm": 64})
    with pytest.raises(ValueError, match="SRAIW shift amount .* out of range"):
        encode_instruction(instructions["sraiw"], {"rd": 1, "rs1": 2, "imm": 32})


def test_encode_instruction_csr_immediate_unsigned_range():
    """CSR immediate is treated as unsigned 12-bit value."""
    instructions = instruction_loader.load_all_instructions()
    csrrw = instructions["csrrw"]
    assert encode_instruction(csrrw, {"rd": 1, "rs1": 2, "imm": 0xC00}) == 0xC00110F3
    with pytest.raises(ValueError, match="CSR immediate .* out of range"):
        encode_instruction(csrrw, {"rd": 1, "rs1": 2, "imm": 0x1000})


def test_encode_instruction_invalid_register_index_too_high():
    """encode_instruction rejects register index > 31."""
    instructions = instruction_loader.load_all_instructions()
    instr = instructions["addi"]
    with pytest.raises(ValueError, match="Register index out of range 0..31: 32"):
        encode_instruction(instr, {"rd": 32, "rs1": 0, "imm": 0})


def test_encode_instruction_invalid_register_index_negative():
    """encode_instruction rejects negative register index."""
    instructions = instruction_loader.load_all_instructions()
    instr = instructions["addi"]
    with pytest.raises(ValueError, match="Register index out of range 0..31: -1"):
        encode_instruction(instr, {"rd": -1, "rs1": 0, "imm": 0})


def test_encode_instruction_invalid_register_type():
    """encode_instruction rejects non-int register operand."""
    instructions = instruction_loader.load_all_instructions()
    instr = instructions["addi"]
    with pytest.raises(ValueError, match="Register operand must be int"):
        encode_instruction(instr, {"rd": "x1", "rs1": 0, "imm": 0})


def test_encode_instruction_b_type_misalignment():
    """encode_instruction raises for B-type immediate not 2-byte aligned."""
    instructions = instruction_loader.load_all_instructions()
    instr = instructions["beq"]
    with pytest.raises(ValueError, match="B-type immediate offset.*not 2-byte aligned"):
        encode_instruction(instr, {"rs1": 1, "rs2": 2, "imm": 9})


def test_encode_instruction_j_type_misalignment():
    """encode_instruction raises for J-type immediate not 2-byte aligned."""
    instructions = instruction_loader.load_all_instructions()
    instr = instructions["jal"]
    with pytest.raises(ValueError, match="J-type immediate offset.*not 2-byte aligned"):
        encode_instruction(instr, {"rd": 1, "imm": 11})
