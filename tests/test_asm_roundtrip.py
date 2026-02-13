# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Test round-trip: asm <-> instance <-> opcode for eumos."""

import pytest

from eumos import instruction_loader
from eumos.decoder import Decoder


@pytest.mark.parametrize(
    "asm_str, expected_opcode",
    [
        ("addi x1, x2, 4", 0x13 | (1 << 7) | (0 << 12) | (2 << 15) | (4 << 20)),
        ("sll x3, x4, x5", 0x33 | (3 << 7) | (1 << 12) | (4 << 15) | (5 << 20)),
        ("sd x6, 8(x7)", 0x23 | (7 << 15) | (3 << 12) | (6 << 20) | (8 << 7)),
        # B-type: beq with 8-byte offset
        ("beq x1, x2, 8", 0x00208263),
        # J-type: jal with 12-byte offset
        ("jal x1, 12", 0x006000EF),
    ],
)
def test_asm_instance_opcode_roundtrip(asm_str, expected_opcode):
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)
    # Parse asm -> instance
    instance = decoder.from_asm(asm_str)
    # Instance -> asm
    asm_out = instance.to_asm()
    assert asm_out == asm_str
    # Instance -> opcode
    opcode = instance.to_opc()
    assert opcode == expected_opcode
    # Decoder round-trip (opcode -> instance)
    instance2 = decoder.from_opc(opcode)
    assert instance2 is not None
    assert instance2.to_asm() == asm_str


def test_b_type_misalignment_raises_error():
    """Test that B-type instructions with odd offsets raise ValueError."""
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)
    # Parse valid asm
    instance = decoder.from_asm("beq x1, x2, 8")
    # Try to encode with odd offset (misaligned)
    instance.operand_values["imm"] = 9  # odd offset
    with pytest.raises(ValueError, match="B-type immediate offset.*not 2-byte aligned"):
        instance.to_opc()


def test_j_type_misalignment_raises_error():
    """Test that J-type instructions with odd offsets raise ValueError."""
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions=instructions)
    # Parse valid asm
    instance = decoder.from_asm("jal x1, 12")
    # Try to encode with odd offset (misaligned)
    instance.operand_values["imm"] = 11  # odd offset
    with pytest.raises(ValueError, match="J-type immediate offset.*not 2-byte aligned"):
        instance.to_opc()
