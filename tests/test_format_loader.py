# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Noodle-Bytes. All Rights Reserved

"""Tests for format_loader.load_format."""

from pathlib import Path

import format_loader
import models


def _format_dir():
    return Path(__file__).resolve().parent.parent / "yaml" / "rv64" / "formats"


def test_load_format_i_returns_format_def():
    fmt = format_loader.load_format(str(_format_dir()), "I")
    assert isinstance(fmt, models.FormatDef)
    assert fmt.name == "I"
    assert fmt.fullname == "Immediate Type"
    assert "{mnemonic}" in fmt.asm_format and "{rd}" in fmt.asm_format
    assert len(fmt.fields) == 5
    rd = next(f for f in fmt.fields if f.name == "rd")
    assert rd.bits == [11, 7]
    assert rd.type == "register"


def test_load_format_s_has_split_imm_with_operand_bits():
    fmt = format_loader.load_format(str(_format_dir()), "S")
    imm = next(f for f in fmt.fields if f.name == "imm")
    assert imm.parts is not None
    assert len(imm.parts) >= 1
    part = imm.parts[0]
    assert part.operand_bits is not None
    assert part.bits is not None


def test_load_format_b_has_split_imm_with_operand_bits():
    fmt = format_loader.load_format(str(_format_dir()), "B")
    imm = next(f for f in fmt.fields if f.name == "imm")
    assert imm.parts is not None
    assert len(imm.parts) >= 1
    part = imm.parts[0]
    assert part.operand_bits is not None
    assert part.bits is not None
