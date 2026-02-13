# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Test Decoder API methods: from_opc and from_asm."""

import pytest

from eumos.decoder import Decoder


def test_decoder_from_opc():
    """Test that Decoder.from_opc() decodes an opcode into an instruction instance."""
    decoder = Decoder()
    opcode = 0x00410093  # addi x1, x2, 4

    instance = decoder.from_opc(opcode)
    assert instance is not None
    assert instance.instruction.mnemonic == "addi"
    assert instance.operand_values["rd"] == 1
    assert instance.operand_values["rs1"] == 2
    assert instance.operand_values["imm"] == 4


def test_decoder_from_asm():
    """Test that Decoder.from_asm() parses assembly strings."""
    decoder = Decoder()

    instance = decoder.from_asm("addi x1, x2, 4")
    assert instance.instruction.mnemonic == "addi"
    assert instance.operand_values["rd"] == 1
    assert instance.operand_values["rs1"] == 2
    assert instance.operand_values["imm"] == 4


def test_decoder_from_asm_unknown_mnemonic():
    """Test that Decoder.from_asm() raises error for unknown mnemonics."""
    decoder = Decoder()

    with pytest.raises(ValueError, match="Unknown instruction mnemonic"):
        decoder.from_asm("foobar x1, x2, x3")


def test_decoder_roundtrip_asm_opc():
    """Test full round-trip: asm -> opc -> asm using Decoder."""
    decoder = Decoder()

    asm = "sll x3, x4, x5"
    instance1 = decoder.from_asm(asm)
    opcode = instance1.to_opc()
    instance2 = decoder.from_opc(opcode)

    assert instance2 is not None
    assert instance2.to_asm() == asm
