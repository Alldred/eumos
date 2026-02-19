# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Tests for Eumos class loading and organization."""

from eumos import Eumos


def test_eumos_loads_all():
    eu = Eumos()
    assert isinstance(eu.csrs, dict)
    assert isinstance(eu.gprs, dict)
    assert isinstance(eu.fprs, dict)
    assert isinstance(eu.formats, dict)
    assert isinstance(eu.instructions, dict)
    assert len(eu.gprs) == 32
    assert len(eu.fprs) == 32
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


def test_eumos_float_extension():
    """F/D extension: FPRs, float group, key mnemonics, and float CSRs."""
    eu = Eumos()
    assert eu.fpr_count == 32
    assert eu.fprs[0].abi_name == "ft0"
    float_instrs = eu.instructions_by_group("float")
    assert len(float_instrs) >= 60
    for mnemonic in (
        "flw",
        "fsw",
        "fadd.s",
        "fadd.d",
        "fmadd.s",
        "fmadd.d",
        "fcvt.w.s",
        "fcvt.d.s",
    ):
        assert mnemonic in eu.instructions, f"missing {mnemonic}"
    assert "R4" in eu.formats
    for name in ("fflags", "frm", "fcsr"):
        assert name in eu.csrs
        assert eu.csrs[name].extension == "F"
    assert "FS" in eu.csrs["mstatus"].fields


def test_gpr_fpr_operand_accessors():
    """InstructionDef and InstructionInstance expose GPR/FPR source and dest operands."""
    from eumos.decoder import Decoder

    eu = Eumos()
    dec = Decoder(eu.instructions)

    # Integer instruction: only GPR
    add = eu.instructions["add"]
    assert set(add.gpr_source_operands()) == {"rs1", "rs2"}
    assert add.gpr_dest_operands() == ["rd"]
    assert add.fpr_source_operands() == []
    assert add.fpr_dest_operands() == []

    # Float load: FPR dest, GPR source (base)
    flw = eu.instructions["flw"]
    assert flw.gpr_source_operands() == ["rs1"]
    assert flw.gpr_dest_operands() == []
    assert flw.fpr_source_operands() == []
    assert flw.fpr_dest_operands() == ["rd"]

    # Float store: FPR source (value), GPR source (base)
    fsw = eu.instructions["fsw"]
    assert fsw.gpr_source_operands() == ["rs1"]
    assert fsw.fpr_source_operands() == ["rs2"]

    # Float arithmetic: FPR only
    fadd = eu.instructions["fadd.s"]
    assert fadd.gpr_source_operands() == []
    assert set(fadd.fpr_source_operands()) == {"rs1", "rs2"}
    assert fadd.fpr_dest_operands() == ["rd"]

    # Compare: GPR dest, FPR sources
    feq = eu.instructions["feq.s"]
    assert feq.gpr_dest_operands() == ["rd"]
    assert set(feq.fpr_source_operands()) == {"rs1", "rs2"}

    # operand_register_bank / operand_banks: executor can choose get/set_fpr vs get/set_gpr from metadata
    assert fadd.operand_register_bank("rd") == "fpr"
    assert fadd.operand_register_bank("rs1") == "fpr"
    assert feq.operand_register_bank("rd") == "gpr"
    assert feq.operand_register_bank("rs1") == "fpr"
    assert fadd.operand_banks() == {"rd": "fpr", "rs1": "fpr", "rs2": "fpr"}

    # Fixed rs2 (encoding-only): not a real FPR source
    fcvt_w_s = eu.instructions["fcvt.w.s"]
    assert fcvt_w_s.fpr_source_operands() == ["rs1"]

    # Instance: decoded values by category
    inst = dec.from_asm("flw f2, 4(x3)")
    assert inst.gpr_sources() == {"rs1": 3}
    assert inst.fpr_dests() == {"rd": 2}

    inst2 = dec.from_asm("fadd.s f1, f2, f3")
    assert inst2.fpr_sources() == {"rs1": 2, "rs2": 3}
    assert inst2.fpr_dests() == {"rd": 1}
