# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Noodle-Bytes. All Rights Reserved

"""User data layered on ISA: instruction instances, register context, and operand-level combined view."""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional

from models import FieldEncoding, InstructionDef, Operand


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


class RegisterContext:
    """Maps register index to user-defined name and/or value (e.g. 1 -> 'gp1', 0x1234)."""

    def __init__(self) -> None:
        self._entries: Dict[int, Dict[str, Any]] = {}

    def set(
        self, reg_index: int, *, name: Optional[str] = None, value: Optional[Any] = None
    ) -> None:
        """Set name and/or value for a register index."""
        if reg_index not in self._entries:
            self._entries[reg_index] = {}
        if name is not None:
            self._entries[reg_index]["name"] = name
        if value is not None:
            self._entries[reg_index]["value"] = value

    def get_name(self, reg_index: int) -> Optional[str]:
        """Return the user-defined name for a register index, or None."""
        return self._entries.get(reg_index, {}).get("name")

    def get_value(self, reg_index: int) -> Optional[Any]:
        """Return the user-defined value for a register index, or None."""
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
