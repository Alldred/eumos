# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Test auto-detection of instructions from asm strings."""

import pytest
from eumos.decoder import Decoder
from eumos import instruction_loader


def test_from_asm_auto_detect():
    """Test that from_asm can auto-detect the instruction from the asm string."""
    # Without passing instruction or instructions dict (auto-loads)
    decoder = Decoder()
    instance = decoder.from_asm("addi x1, x2, 4")
    assert instance.instruction.mnemonic == "addi"
    assert instance.operand_values["rd"] == 1
    assert instance.operand_values["rs1"] == 2
    assert instance.operand_values["imm"] == 4
    assert instance.to_asm() == "addi x1, x2, 4"


def test_from_asm_auto_detect_with_instructions():
    """Test that from_asm can auto-detect when instructions dict is provided."""
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)
    
    instance = decoder.from_asm("sll x3, x4, x5")
    assert instance.instruction.mnemonic == "sll"
    assert instance.operand_values["rd"] == 3
    assert instance.operand_values["rs1"] == 4
    assert instance.operand_values["rs2"] == 5


def test_from_asm_unknown_mnemonic():
    """Test that from_asm raises an error for unknown mnemonics."""
    decoder = Decoder()
    with pytest.raises(ValueError, match="Unknown instruction mnemonic"):
        decoder.from_asm("foobar x1, x2, x3")


def test_from_asm_explicit_instruction_still_works():
    """Test that decoder can parse any valid asm string."""
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)
    
    instance = decoder.from_asm("addi x1, x2, 4")
    assert instance.instruction.mnemonic == "addi"
    assert instance.operand_values["rd"] == 1
