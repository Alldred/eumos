# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Tests for Eumos class loading and organization."""

from eumos import Eumos


def test_eumos_loads_all():
    eu = Eumos()
    assert isinstance(eu.csrs, dict)
    assert isinstance(eu.gprs, dict)
    assert isinstance(eu.formats, dict)
    assert isinstance(eu.instructions, dict)
    assert len(eu.gprs) == 32
    assert len(eu.csrs) > 0
    assert len(eu.formats) > 0
    assert len(eu.instructions) > 0


def test_eumos_gpr_example():
    eu = Eumos()
    gpr = eu.gprs[0]
    assert gpr.abi_name == "zero"
    assert gpr.index == 0
    assert gpr.access == "read-only"


def test_eumos_csr_example():
    eu = Eumos()
    assert "mstatus" in eu.csrs
    mstatus = eu.csrs["mstatus"]
    assert mstatus.address == 0x300
    assert mstatus.privilege == "machine"


def test_eumos_instruction_example():
    eu = Eumos()
    assert "addi" in eu.instructions
    addi = eu.instructions["addi"]
    assert addi.mnemonic == "addi"
    assert "rd" in addi.operands
    assert "imm" in addi.operands


def test_eumos_format_example():
    eu = Eumos()
    assert "I" in eu.formats
    fmt = eu.formats["I"]
    assert fmt.name == "I"
    assert "rd" in [f.name for f in fmt.fields]
