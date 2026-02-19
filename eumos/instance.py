# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""User data layered on ISA: instruction instances, register context, and operand-level combined view."""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple, Union

from .constants import FPR_NAME_TO_INDEX, GPR_ABI_NAMES, GPR_NAME_TO_INDEX
from .encoder import encode_instruction
from .models import CSRDef, FieldEncoding, FPRDef, GPRDef, InstructionDef, Operand

# Lazy-loaded GPR definitions (index -> GPRDef) for reset_value and access lookup.
_GPR_DEFS: Optional[Dict[int, GPRDef]] = None

# Lazy-loaded FPR definitions (index -> FPRDef).
_FPR_DEFS: Optional[Dict[int, FPRDef]] = None


def get_gpr_def(reg_index: int) -> Optional[GPRDef]:
    """Return GPR definition for index 0..31 (reset value, access), or None. Loads GPR YAML on first use."""
    global _GPR_DEFS
    if _GPR_DEFS is None:
        try:
            from . import gpr_loader

            _GPR_DEFS = gpr_loader.load_all_gprs()
        except Exception:
            _GPR_DEFS = {}
    if not (0 <= reg_index <= 31):
        return None
    return _GPR_DEFS.get(reg_index)


def get_fpr_def(reg_index: int) -> Optional[FPRDef]:
    """Return FPR definition for index 0..31 (reset value, access), or None. Loads FPR YAML on first use."""
    global _FPR_DEFS
    if _FPR_DEFS is None:
        try:
            from . import fpr_loader

            _FPR_DEFS = fpr_loader.load_all_fprs()
        except Exception:
            _FPR_DEFS = {}
    if not (0 <= reg_index <= 31):
        return None
    return _FPR_DEFS.get(reg_index)


def _fpr_to_index(reg: Union[int, str]) -> Optional[int]:
    """Resolve register to FPR index (0..31). Accepts int index or RISC-V name (e.g. 'fa0', 'f10')."""
    if isinstance(reg, int):
        if 0 <= reg <= 31:
            return reg
        return None
    idx = FPR_NAME_TO_INDEX.get(reg.lower())
    return idx


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
    idx = GPR_NAME_TO_INDEX.get(reg.lower())
    return idx


class RegisterContext:
    """Maps GPR index (0..31) to RISC-V GPR name and optional value. Use index or name when setting."""

    def __init__(
        self,
        gpr_defs: Optional[Union[Dict[int, GPRDef], Iterable[GPRDef]]] = None,
    ) -> None:
        self._entries: Dict[int, Dict[str, Any]] = {}
        self._gpr_defs: Optional[Dict[int, GPRDef]] = None
        if gpr_defs is not None:
            if isinstance(gpr_defs, dict):
                self._gpr_defs = gpr_defs
            else:
                self._gpr_defs = {g.index: g for g in gpr_defs}

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
        return self._entries.get(reg_index, {}).get("name") or GPR_ABI_NAMES[reg_index]

    def get_value(self, reg_index: int) -> Optional[Any]:
        """Return the user-set value for a register index, or None."""
        return self._entries.get(reg_index, {}).get("value")

    def get_reset_value(self, reg_index: int) -> Optional[int]:
        """Return the reset value for a register index from GPR spec, or None."""
        if not 0 <= reg_index <= 31:
            return None
        if self._gpr_defs is not None:
            g = self._gpr_defs.get(reg_index)
            return g.reset_value if g else None
        g = get_gpr_def(reg_index)
        return g.reset_value if g else None

    def get_access(self, reg_index: int) -> Optional[str]:
        """Return the access (e.g. read-only, read-write) for a register index from GPR spec, or None."""
        if not 0 <= reg_index <= 31:
            return None
        if self._gpr_defs is not None:
            g = self._gpr_defs.get(reg_index)
            return g.access if g else None
        g = get_gpr_def(reg_index)
        return g.access if g else None


def _csr_key_to_address(
    key: Union[int, str], csr_defs: Optional[Dict[str, CSRDef]]
) -> Optional[int]:
    """Resolve CSR key (address or name) to 12-bit address, or None."""
    if isinstance(key, int):
        if 0 <= key <= 0xFFF:
            return key
        return None
    if isinstance(key, str) and csr_defs is not None:
        csr = csr_defs.get(key)
        return csr.address if csr else None
    return None


class CSRContext:
    """Maps CSR address or name to runtime value. Optionally takes CSR definitions for name/address resolution."""

    def __init__(
        self,
        csr_defs: Optional[Union[Dict[str, CSRDef], Iterable[CSRDef]]] = None,
    ) -> None:
        self._values: Dict[int, Any] = {}
        self._csr_by_name: Dict[str, CSRDef] = {}
        if csr_defs is not None:
            if isinstance(csr_defs, dict):
                self._csr_by_name = csr_defs
            else:
                self._csr_by_name = {c.name: c for c in csr_defs}
        self._csr_by_address = {c.address: c for c in self._csr_by_name.values()}

    def set(self, address_or_name: Union[int, str], value: Any) -> None:
        """Set the value for a CSR by 12-bit address or by name (if definitions were provided)."""
        addr = _csr_key_to_address(address_or_name, self._csr_by_name or None)
        if addr is not None:
            self._values[addr] = value

    def get_value(self, address_or_name: Union[int, str]) -> Optional[Any]:
        """Return the value for a CSR by address or name, or None."""
        addr = _csr_key_to_address(address_or_name, self._csr_by_name or None)
        if addr is None:
            return None
        return self._values.get(addr)

    def get_address(self, name: str) -> Optional[int]:
        """Return the 12-bit address for a CSR name, or None if definitions were not provided or name unknown."""
        csr = self._csr_by_name.get(name) if self._csr_by_name else None
        return csr.address if csr else None

    def get_name(self, address: int) -> Optional[str]:
        """Return the CSR name for a 12-bit address, or None if definitions were not provided or address unknown."""
        csr = (
            self._csr_by_address.get(address & 0xFFF) if self._csr_by_address else None
        )
        return csr.name if csr else None


@dataclass
class ISA:
    """Container for optional instructions and/or CSRs; either can be loaded separately."""

    instructions: Optional[Dict[str, InstructionDef]] = None
    csrs: Optional[Dict[str, CSRDef]] = None
    csrs_by_address: Optional[Dict[int, CSRDef]] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.csrs is not None and self.csrs_by_address is None:
            object.__setattr__(
                self,
                "csrs_by_address",
                {csr.address: csr for csr in self.csrs.values()},
            )

    def resolve_csr(
        self,
        instruction_instance: "InstructionInstance",
        csr_context: Optional[CSRContext] = None,
    ) -> Tuple[Optional[CSRDef], Optional[Any]]:
        """Resolve the CSR for a CSR instruction (using imm operand) to CSRDef and optional value from context."""
        if self.csrs_by_address is None:
            return None, None
        imm = instruction_instance.operand_values.get("imm")
        if imm is None:
            return None, None
        addr = int(imm) & 0xFFF
        csr_def = self.csrs_by_address.get(addr)
        if csr_def is None:
            return None, None
        value = csr_context.get_value(addr) if csr_context else None
        return csr_def, value


@dataclass
class InstructionInstance:
    """Concrete decoded instruction instance with bound operand values and related metadata.

    Attributes:
        instruction: The instruction definition from the ISA
        operand_values: Dict mapping operand names to their runtime values
        register_context: Optional register context for resolving register names/values
        pc: Optional program counter value
    """

    def to_asm(self) -> str:
        """Return the assembly string for this instruction instance."""
        fmt = self.instruction.format
        fmt_entry = fmt.asm_formats[self.instruction.asm_format]
        operand_names = fmt_entry["operands"]
        offset_base = fmt_entry.get("offset_base", False)

        # Build operand strings
        operand_strs = []
        for op_name in operand_names:
            value = self.operand_values.get(op_name)
            if value is None:
                raise ValueError(f"Missing operand value for {op_name}")
            op = self.instruction.operands.get(op_name)
            if op and op.type == "register":
                operand_strs.append(
                    f"f{value}"
                    if self.instruction.is_operand_fpr(op_name)
                    else f"x{value}"
                )
            else:
                operand_strs.append(str(value))

        # Format assembly string
        mnemonic = self.instruction.mnemonic

        # Handle zero-operand instructions
        if len(operand_strs) == 0:
            return mnemonic

        if offset_base and len(operand_strs) >= 2:
            # offset_base format: "mnemonic op1, imm(base)"
            # Last two operands are offset and base
            offset = operand_strs[-2]
            base = operand_strs[-1]
            rest = operand_strs[:-2]
            if rest:
                return f"{mnemonic} {', '.join(rest)}, {offset}({base})"
            else:
                return f"{mnemonic} {offset}({base})"
        else:
            # Standard comma-separated format
            return f"{mnemonic} {', '.join(operand_strs)}"

    def asm(self) -> str:
        """Alias for to_asm() for backwards compatibility."""
        return self.to_asm()

    def to_opc(self) -> int:
        """Pack this instruction instance into a 32-bit opcode."""
        return encode_instruction(self.instruction, self.operand_values)

    def gpr_sources(self) -> Dict[str, Any]:
        """GPR (integer) source operand names -> decoded values. E.g. {'rs1': 2} for base register."""
        return {
            name: self.operand_values[name]
            for name in self.instruction.gpr_source_operands()
            if name in self.operand_values
        }

    def gpr_dests(self) -> Dict[str, Any]:
        """GPR (integer) destination operand names -> decoded values. E.g. {'rd': 1}."""
        return {
            name: self.operand_values[name]
            for name in self.instruction.gpr_dest_operands()
            if name in self.operand_values
        }

    def fpr_sources(self) -> Dict[str, Any]:
        """FPR (float) source operand names -> decoded values. E.g. {'rs1': 2, 'rs2': 3}."""
        return {
            name: self.operand_values[name]
            for name in self.instruction.fpr_source_operands()
            if name in self.operand_values
        }

    def fpr_dests(self) -> Dict[str, Any]:
        """FPR (float) destination operand names -> decoded values. E.g. {'rd': 1}."""
        return {
            name: self.operand_values[name]
            for name in self.instruction.fpr_dest_operands()
            if name in self.operand_values
        }

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
