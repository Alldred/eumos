# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Noodle-Bytes. All Rights Reserved

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""User data layered on ISA: instruction instances, register context, and operand-level combined view."""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional, Union

from models import FieldEncoding, InstructionDef, Operand

# RISC-V GPR ABI names (x0..x31). s0/fp is canonical as s0.
_GPR_ABI_NAMES = (
    "zero",
    "ra",
    "sp",
    "gp",
    "tp",
    "t0",
    "t1",
    "t2",
    "s0",
    "s1",
    "a0",
    "a1",
    "a2",
    "a3",
    "a4",
    "a5",
    "a6",
    "a7",
    "s2",
    "s3",
    "s4",
    "s5",
    "s6",
    "s7",
    "s8",
    "s9",
    "s10",
    "s11",
    "t3",
    "t4",
    "t5",
    "t6",
)
_GPR_NAME_TO_INDEX: Dict[str, int] = {}
for _i, _n in enumerate(_GPR_ABI_NAMES):
    _GPR_NAME_TO_INDEX[_n] = _i
for _i in range(32):
    _GPR_NAME_TO_INDEX[f"x{_i}"] = _i
_GPR_NAME_TO_INDEX["fp"] = 8  # s0/fp


@dataclass
class OperandInfo:
    """Combined view for one operand: ISA (name, type, size, encoding) plus user value and optional resolved name/value."""

    name: str
    type: str
    size: int
    bits: Any = None
    parts: Optional[list] = None  # List[FieldPart] from encoding
    value: Optional[Any] = None
    resolved_name: Optional[str] = None
    resolved_value: Optional[Any] = None


def _reg_to_index(reg: Union[int, str]) -> Optional[int]:
    """Resolve register to GPR index (0..31). Accepts int index or RISC-V name (e.g. 'ra', 'x1')."""
    if isinstance(reg, int):
        if 0 <= reg <= 31:
            return reg
        return None
    idx = _GPR_NAME_TO_INDEX.get(reg.lower())
    return idx


class RegisterContext:
    """Maps GPR index (0..31) to RISC-V GPR name and optional value. Use index or name when setting."""

    def __init__(self) -> None:
        self._entries: Dict[int, Dict[str, Any]] = {}

    def set(
        self,
        reg: Union[int, str],
        *,
        name: Optional[str] = None,
        value: Optional[Any] = None,
    ) -> None:
        """Set name and/or value for a register. reg is GPR index (0..31) or RISC-V name (e.g. 'ra', 'x1')."""
        reg_index = _reg_to_index(reg)
        if reg_index is None:
            return
        if reg_index not in self._entries:
            self._entries[reg_index] = {}
        if name is not None:
            self._entries[reg_index]["name"] = name
        if value is not None:
            self._entries[reg_index]["value"] = value

    def get_name(self, reg_index: int) -> Optional[str]:
        """Return the name for a register index: user-set name if any, else RISC-V ABI name (e.g. 'ra')."""
        if not 0 <= reg_index <= 31:
            return None
        return self._entries.get(reg_index, {}).get("name") or _GPR_ABI_NAMES[reg_index]

    def get_value(self, reg_index: int) -> Optional[Any]:
        """Return the user-set value for a register index, or None."""
        return self._entries.get(reg_index, {}).get("value")


@dataclass
class InstructionInstance:
    """One instance of an instruction with concrete operand values; ISA and user data kept separate, combined at operand level."""

    instruction: InstructionDef
    operand_values: Dict[str, Any] = field(default_factory=dict)
    register_context: Optional[RegisterContext] = None
    pc: Optional[int] = None

    def get_operand_info(self, name: str) -> Optional[OperandInfo]:
        """Return combined ISA + user info for one operand, or None if the operand is not defined."""
        if name not in self.instruction.operands:
            return None
        op: Operand = self.instruction.operands[name]
        enc: Optional[FieldEncoding] = self.instruction.fields.get(name)
        bits = enc.bits if enc else None
        parts = enc.parts if enc else None
        value = self.operand_values.get(name)
        resolved_name: Optional[str] = None
        resolved_value: Optional[Any] = None
        if (
            op.type == "register"
            and value is not None
            and self.register_context is not None
        ):
            try:
                idx = int(value)
                resolved_name = self.register_context.get_name(idx)
                resolved_value = self.register_context.get_value(idx)
            except (TypeError, ValueError):
                pass
        return OperandInfo(
            name=op.name,
            type=op.type,
            size=op.size,
            bits=bits,
            parts=parts,
            value=value,
            resolved_name=resolved_name,
            resolved_value=resolved_value,
        )

    def operands(self) -> Iterator[OperandInfo]:
        """Yield OperandInfo for each operand (inputs first, then remaining operands)."""
        seen = set()
        for name in self.instruction.inputs:
            if name not in seen and (info := self.get_operand_info(name)) is not None:
                seen.add(name)
                yield info
        for name in self.instruction.operands:
            if name not in seen and (info := self.get_operand_info(name)) is not None:
                seen.add(name)
                yield info
