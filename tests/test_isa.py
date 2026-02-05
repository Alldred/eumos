# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Tests for instance.CSRContext and ISA (load instructions/CSRs separately or together, resolve_csr)."""

from pathlib import Path

import csr_loader
import instruction_loader
from decoder import Decoder
from instance import ISA, CSRContext


def _paths():
    repo = Path(__file__).resolve().parent.parent
    return {
        "format_dir": repo / "yaml" / "rv64" / "formats",
        "instr_root": repo / "yaml" / "rv64" / "instructions",
        "csr_root": repo / "yaml" / "rv64" / "csrs",
    }


def test_csr_context_set_get_by_address():
    """CSRContext stores and returns values by 12-bit address without definitions."""
    ctx = CSRContext()
    ctx.set(0x300, 0x1234)
    assert ctx.get_value(0x300) == 0x1234
    assert ctx.get_value(0x341) is None
    assert ctx.get_name(0x300) is None  # no definitions


def test_csr_context_set_get_by_name_when_definitions_provided():
    """CSRContext resolves name to address when built with csr_defs."""
    p = _paths()
    csrs = csr_loader.load_all_csrs(str(p["csr_root"]))
    ctx = CSRContext(csr_defs=csrs)
    ctx.set("mstatus", 0x88)
    assert ctx.get_value("mstatus") == 0x88
    assert ctx.get_value(0x300) == 0x88
    assert ctx.get_address("mstatus") == 0x300
    assert ctx.get_name(0x300) == "mstatus"
    assert ctx.get_name(0x341) == "mepc"


def test_isa_instructions_only():
    """ISA can hold only instructions; csrs and csrs_by_address are None."""
    p = _paths()
    instrs = instruction_loader.load_all_instructions(
        str(p["instr_root"]), str(p["format_dir"])
    )
    isa = ISA(instructions=instrs)
    assert isa.instructions is not None
    assert len(isa.instructions) == 60
    assert isa.csrs is None
    assert isa.csrs_by_address is None


def test_isa_csrs_only():
    """ISA can hold only CSRs; instructions None, csrs_by_address populated."""
    p = _paths()
    csrs = csr_loader.load_all_csrs(str(p["csr_root"]))
    isa = ISA(csrs=csrs)
    assert isa.instructions is None
    assert isa.csrs is not None
    assert isa.csrs_by_address is not None
    assert isa.csrs_by_address[0x300].name == "mstatus"
    assert isa.csrs_by_address[0x341].name == "mepc"


def test_isa_both_loaded():
    """ISA can hold both instructions and CSRs; csrs_by_address built from csrs."""
    p = _paths()
    instrs = instruction_loader.load_all_instructions(
        str(p["instr_root"]), str(p["format_dir"])
    )
    csrs = csr_loader.load_all_csrs(str(p["csr_root"]))
    isa = ISA(instructions=instrs, csrs=csrs)
    assert isa.instructions is not None
    assert isa.csrs is not None
    assert isa.csrs_by_address is not None
    assert isa.csrs_by_address[0x300].name == "mstatus"


def test_resolve_csr_decode_csrrw_then_resolve():
    """Decode a CSR instruction (csrrw), then resolve CSR def and value via ISA + CSRContext."""
    p = _paths()
    instrs = instruction_loader.load_all_instructions(
        str(p["instr_root"]), str(p["format_dir"])
    )
    csrs = csr_loader.load_all_csrs(str(p["csr_root"]))
    isa = ISA(instructions=instrs, csrs=csrs)
    dec = Decoder(instructions=isa.instructions)
    # csrrw rd, 0x341, rs1  -> CSRRW with imm=0x341 (mepc); opcode=0x73, funct3=1, rd, rs1, imm
    # I-type: imm [31:20], rs1 [19:15], funct3 [14:12], rd [11:7], opcode [6:0]
    word = 0x73 | (1 << 7) | (1 << 12) | (2 << 15) | (0x341 << 20)
    instance = dec.decode(word)
    assert instance is not None
    assert instance.instruction.mnemonic == "csrrw"
    assert instance.operand_values.get("imm") is not None
    csr_def, value = isa.resolve_csr(instance)
    assert csr_def is not None
    assert csr_def.name == "mepc"
    assert csr_def.address == 0x341
    assert value is None  # no context
    ctx = CSRContext(csrs)
    ctx.set("mepc", 0x1000)
    csr_def2, value2 = isa.resolve_csr(instance, csr_context=ctx)
    assert csr_def2.name == "mepc"
    assert value2 == 0x1000
