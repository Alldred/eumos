# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Tests for instance.InstructionInstance, RegisterContext, OperandInfo (operand-level combination)."""

from eumos import instruction_loader
from eumos.instance import (
    InstructionInstance,
    OperandInfo,
    RegisterContext,
    get_gpr_def,
)


def test_storage_separate_isa_has_no_user_fields():
    """ISA types (InstructionDef, Operand) have no user data fields."""
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["addi"]
    assert hasattr(instr, "operands") and hasattr(instr, "fields")
    assert not hasattr(instr, "operand_values")
    op = instr.operands["rs1"]
    assert (
        not hasattr(op, "value") or getattr(op, "data", None) is None
    )  # data is fixed ISA, not user value


def test_get_operand_info_combines_isa_and_user():
    """get_operand_info returns OperandInfo with ISA (name, type, size, encoding) and user value."""
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["addi"]
    operand_values = {"rd": 3, "rs1": 1, "imm": 0x100}
    instance = InstructionInstance(instruction=instr, operand_values=operand_values)
    rs1 = instance.get_operand_info("rs1")
    assert rs1 is not None
    assert isinstance(rs1, OperandInfo)
    assert rs1.name == "rs1"
    assert rs1.type == "register"
    assert rs1.size == 5
    assert rs1.bits == [19, 15]
    assert rs1.value == 1
    assert rs1.resolved_name is None
    assert rs1.resolved_value is None


def test_get_operand_info_resolves_register_via_context():
    """For register operands, OperandInfo includes resolved_name and resolved_value from RegisterContext."""
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["addi"]
    operand_values = {"rd": 3, "rs1": 1, "imm": 0x100}
    regs = RegisterContext()
    regs.set(1, name="gp1", value=0x1234)
    instance = InstructionInstance(
        instruction=instr,
        operand_values=operand_values,
        register_context=regs,
    )
    rs1 = instance.get_operand_info("rs1")
    assert rs1 is not None
    assert rs1.value == 1
    assert rs1.resolved_name == "gp1"
    assert rs1.resolved_value == 0x1234


def test_register_context_maps_gpr_index_to_riscv_name():
    """RegisterContext maps GPR index to RISC-V ABI name; get_name returns it when no override."""
    regs = RegisterContext()
    assert regs.get_name(0) == "zero"
    assert regs.get_name(1) == "ra"
    assert regs.get_name(2) == "sp"
    assert regs.get_name(8) == "s0"
    assert regs.get_name(10) == "a0"


def test_register_context_set_accepts_index_or_name():
    """set() accepts either GPR index (int) or RISC-V name (e.g. 'ra', 'x1')."""
    regs = RegisterContext()
    regs.set(1, value=0x1000)
    assert regs.get_name(1) == "ra"
    assert regs.get_value(1) == 0x1000
    regs.set("sp", value=0x8000)
    assert regs.get_name(2) == "sp"
    assert regs.get_value(2) == 0x8000
    regs.set("x5", value=0x5555)
    assert regs.get_name(5) == "t0"
    assert regs.get_value(5) == 0x5555


def test_operands_yields_operand_info_per_operand():
    """operands() yields OperandInfo for each operand; combined view at operand level."""
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["addi"]
    operand_values = {"rd": 3, "rs1": 1, "imm": 0x100}
    instance = InstructionInstance(instruction=instr, operand_values=operand_values)
    infos = list(instance.operands())
    names = [info.name for info in infos]
    assert "rd" in names
    assert "rs1" in names
    assert "imm" in names
    for info in infos:
        assert isinstance(info, OperandInfo)
        assert info.name and info.type and info.size >= 0


def test_instruction_only_isa_uses_instruction_def_operands():
    """Callers that only need ISA use InstructionDef.operands; no user data there."""
    instrs = instruction_loader.load_all_instructions()
    instr = instrs["addi"]
    assert "rs1" in instr.operands
    assert instr.operands["rs1"].type == "register"
    assert instr.operands["rs1"].size == 5


def test_get_gpr_def_returns_reset_and_access():
    """get_gpr_def returns GPRDef with reset_value and access from GPR YAML."""
    g0 = get_gpr_def(0)
    assert g0 is not None
    assert g0.index == 0
    assert g0.abi_name == "zero"
    assert g0.reset_value == 0
    assert g0.access == "read-only"
    g1 = get_gpr_def(1)
    assert g1 is not None
    assert g1.access == "read-write"
    assert get_gpr_def(32) is None


def test_register_context_get_reset_value_and_access():
    """RegisterContext.get_reset_value and get_access use GPR spec when available."""
    regs = RegisterContext()
    assert regs.get_reset_value(0) == 0
    assert regs.get_access(0) == "read-only"
    assert regs.get_reset_value(1) == 0
    assert regs.get_access(1) == "read-write"
    assert regs.get_reset_value(32) is None
    assert regs.get_access(32) is None
