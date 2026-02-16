# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Tests for zero-operand instructions and register validation."""

import pytest

from eumos import instruction_loader
from eumos.decoder import Decoder


def test_zero_operand_ecall():
    """Test parsing and encoding of ecall (zero-operand instruction)."""
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)

    # Parse ecall
    instance = decoder.from_asm("ecall")
    assert instance.instruction.mnemonic == "ecall"
    assert instance.operand_values == {}

    # Round-trip through asm
    asm_out = instance.to_asm()
    assert asm_out == "ecall"

    # Encode to opcode
    opcode = instance.to_opc()
    assert opcode == 0x00000073  # ECALL encoding

    # Decode back - decoder should now distinguish ecall from ebreak/mret
    instance2 = decoder.from_opc(opcode)
    assert instance2 is not None
    assert instance2.instruction.mnemonic == "ecall"
    assert instance2.to_asm() == "ecall"


def test_zero_operand_ebreak():
    """Test parsing and encoding of ebreak (zero-operand instruction)."""
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)

    # Parse ebreak
    instance = decoder.from_asm("ebreak")
    assert instance.instruction.mnemonic == "ebreak"
    assert instance.operand_values == {}

    # Round-trip through asm
    assert instance.to_asm() == "ebreak"

    # Encode to opcode
    opcode = instance.to_opc()
    assert opcode == 0x00100073  # EBREAK encoding

    # Decode back - decoder should now distinguish ebreak from ecall/mret
    instance2 = decoder.from_opc(opcode)
    assert instance2 is not None
    assert instance2.instruction.mnemonic == "ebreak"
    assert instance2.to_asm() == "ebreak"


def test_zero_operand_mret():
    """Test parsing and encoding of mret (zero-operand instruction)."""
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)

    # Parse mret
    instance = decoder.from_asm("mret")
    assert instance.instruction.mnemonic == "mret"
    assert instance.operand_values == {}

    # Round-trip
    assert instance.to_asm() == "mret"
    opcode = instance.to_opc()
    assert opcode == 0x30200073  # MRET encoding

    instance2 = decoder.from_opc(opcode)
    assert instance2.to_asm() == "mret"


def test_zero_operand_case_insensitive():
    """Test that zero-operand instructions are case-insensitive."""
    decoder = Decoder()

    # Should accept different cases
    for mnemonic in ["ECALL", "Ecall", "EcAlL"]:
        instance = decoder.from_asm(mnemonic)
        assert instance.instruction.mnemonic == "ecall"
        assert instance.to_asm() == "ecall"  # Normalized to lowercase


def test_invalid_register_x32():
    """Test that x32 raises ValueError (out of range)."""
    decoder = Decoder()

    with pytest.raises(ValueError, match="Register index 32 out of range"):
        decoder.from_asm("addi x32, x1, 4")


def test_invalid_register_x33():
    """Test that x33 raises ValueError (out of range)."""
    decoder = Decoder()

    with pytest.raises(ValueError, match="Register index 33 out of range"):
        decoder.from_asm("add x1, x2, x33")


def test_invalid_register_x100():
    """Test that x100 raises ValueError (out of range)."""
    decoder = Decoder()

    with pytest.raises(ValueError, match="Register index 100 out of range"):
        decoder.from_asm("sll x1, x100, x3")


def test_invalid_register_in_to_opc():
    """Test that to_opc() validates register range."""
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)

    # Create a valid instance
    instance = decoder.from_asm("addi x1, x2, 4")

    # Manually set an invalid register value
    instance.operand_values["rd"] = 32  # Out of range

    with pytest.raises(ValueError, match="Register index out of range 0..31: 32"):
        instance.to_opc()


def test_invalid_register_negative():
    """Test that negative register index is rejected in to_opc()."""
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)

    instance = decoder.from_asm("add x1, x2, x3")
    instance.operand_values["rs1"] = -1  # Invalid

    with pytest.raises(ValueError, match="Register index out of range 0..31: -1"):
        instance.to_opc()


def test_valid_register_x31():
    """Test that x31 is valid (boundary test)."""
    decoder = Decoder()

    # x31 should be valid
    instance = decoder.from_asm("addi x31, x31, 4")
    assert instance.operand_values["rd"] == 31
    assert instance.operand_values["rs1"] == 31

    # Should round-trip correctly
    opcode = instance.to_opc()
    instance2 = decoder.from_opc(opcode)
    assert instance2.to_asm() == "addi x31, x31, 4"


def test_valid_register_x0():
    """Test that x0 is valid (boundary test)."""
    decoder = Decoder()

    # x0 should be valid
    instance = decoder.from_asm("addi x0, x1, 4")
    assert instance.operand_values["rd"] == 0
    assert instance.operand_values["rs1"] == 1

    # Should round-trip correctly
    opcode = instance.to_opc()
    instance2 = decoder.from_opc(opcode)
    assert instance2.to_asm() == "addi x0, x1, 4"


def test_invalid_register_in_load_store():
    """Test that invalid registers in load/store instructions are rejected."""
    decoder = Decoder()

    # Invalid register in load instruction
    with pytest.raises(ValueError, match="Register index 32 out of range"):
        decoder.from_asm("ld x32, 8(x7)")

    # Invalid base register
    with pytest.raises(ValueError, match="Register index 40 out of range"):
        decoder.from_asm("sd x6, 8(x40)")
