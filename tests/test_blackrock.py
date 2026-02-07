# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Tests for Blackrock class loading and organization."""

from blackrock import Blackrock


def test_blackrock_loads_all():
    br = Blackrock()
    assert isinstance(br.csrs, dict)
    assert isinstance(br.gprs, dict)
    assert isinstance(br.formats, dict)
    assert isinstance(br.instructions, dict)
    assert len(br.gprs) == 32
    assert len(br.csrs) > 0
    assert len(br.formats) > 0
    assert len(br.instructions) > 0


def test_blackrock_gpr_example():
    br = Blackrock()
    gpr = br.gprs[0]
    assert gpr.abi_name == "zero"
    assert gpr.index == 0
    assert gpr.access == "read-only"


def test_blackrock_csr_example():
    br = Blackrock()
    assert "mstatus" in br.csrs
    mstatus = br.csrs["mstatus"]
    assert mstatus.address == 0x300
    assert mstatus.privilege == "machine"


def test_blackrock_instruction_example():
    br = Blackrock()
    assert "addi" in br.instructions
    addi = br.instructions["addi"]
    assert addi.mnemonic == "addi"
    assert "rd" in addi.operands
    assert "imm" in addi.operands


def test_blackrock_format_example():
    br = Blackrock()
    assert "I" in br.formats
    fmt = br.formats["I"]
    assert fmt.name == "I"
    assert "rd" in [f.name for f in fmt.fields]
