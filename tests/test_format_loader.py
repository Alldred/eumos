# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Tests for format_loader.load_all_formats."""

from eumos import format_loader, models


def test_load_format_i_returns_format_def():
    formats = format_loader.load_all_formats()
    fmt = formats["I"]
    assert isinstance(fmt, models.FormatDef)
    assert fmt.name == "I"
    assert fmt.fullname == "Immediate Type"
    assert "{mnemonic}" in fmt.asm_format and "{rd}" in fmt.asm_format
    assert len(fmt.fields) == 5
    rd = next(f for f in fmt.fields if f.name == "rd")
    assert rd.bits == [11, 7]
    assert rd.type == "register"


def test_load_format_s_has_split_imm_with_operand_bits():
    formats = format_loader.load_all_formats()
    fmt = formats["S"]
    imm = next(f for f in fmt.fields if f.name == "imm")
    assert imm.parts is not None
    assert len(imm.parts) >= 1
    part = imm.parts[0]
    assert part.operand_bits is not None
    assert part.bits is not None


def test_load_format_b_has_split_imm_with_operand_bits():
    formats = format_loader.load_all_formats()
    fmt = formats["B"]
    imm = next(f for f in fmt.fields if f.name == "imm")
    assert imm.parts is not None
    assert len(imm.parts) >= 1
    part = imm.parts[0]
    assert part.operand_bits is not None
    assert part.bits is not None
