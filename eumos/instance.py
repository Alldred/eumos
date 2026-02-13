# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""User data layered on ISA: instruction instances, register context, and operand-level combined view."""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple, Union

from .models import CSRDef, FieldEncoding, GPRDef, InstructionDef, Operand

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

# Lazy-loaded GPR definitions (index -> GPRDef) for reset_value and access lookup.
_GPR_DEFS: Optional[Dict[int, GPRDef]] = None


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
        return self._entries.get(reg_index, {}).get("name") or _GPR_ABI_NAMES[reg_index]

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
        asm_formats = getattr(fmt, "asm_formats", None)
        if not asm_formats:
            raise ValueError(f"No asm_formats defined for format {fmt.name}")

        # Use asm_format from instruction definition if specified
        format_name = getattr(self.instruction, "asm_format", None)
        if format_name is None:
            # Prefer well-known keys for deterministic fallback
            if "default" in asm_formats:
                format_name = "default"
            elif "standard" in asm_formats:
                format_name = "standard"
            else:
                # Last resort: use any available format
                format_name = next(iter(asm_formats))

        if format_name not in asm_formats:
            raise ValueError(
                f"Unknown asm_format '{format_name}' for format {fmt.name}"
            )

        fmt_entry = asm_formats[format_name]
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
                operand_strs.append(f"x{value}")
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
        word = 0
        # First, encode fixed values (opcode, funct3, funct7, etc.)
        for field_name, value in self.instruction.fixed_values.items():
            encoding = self.instruction.fields.get(field_name)
            if encoding and encoding.bits:
                bits = encoding.bits
                if len(bits) == 2:
                    msb, lsb = bits
                    mask = (1 << (abs(msb - lsb) + 1)) - 1
                    word |= (value & mask) << lsb
                else:
                    word |= (value & 1) << bits[0]

        # Encode operand values
        fmt_name = self.instruction.format.name
        for op_name, op_value in self.operand_values.items():
            encoding = self.instruction.fields.get(op_name)
            if not encoding:
                continue

            # Prepare the raw value to encode
            raw_value = op_value
            if encoding.type == "immediate":
                # Undo sign extension and scaling for branch/jump
                if fmt_name == "B":
                    # 13-bit signed, scaled by 2; require 2-byte alignment
                    if op_value % 2 != 0:
                        raise ValueError(
                            f"B-type immediate offset {op_value} is not 2-byte aligned and cannot be encoded"
                        )
                    raw_value = (op_value // 2) & 0x1FFF
                elif fmt_name == "J":
                    # 21-bit signed, scaled by 2; require 2-byte alignment
                    if op_value % 2 != 0:
                        raise ValueError(
                            f"J-type immediate offset {op_value} is not 2-byte aligned and cannot be encoded"
                        )
                    raw_value = (op_value // 2) & 0x1FFFFF
                elif fmt_name == "U":
                    # 20-bit at [31:12], no scaling
                    raw_value = op_value & 0xFFFFF
                elif fmt_name in ("I", "S"):
                    # 12-bit signed
                    raw_value = op_value & 0xFFF

            # Encode into bit positions
            if encoding.parts:
                # Multi-part encoding (e.g., S-type, B-type, J-type immediates)
                for part in encoding.parts:
                    instr_bits = part.bits
                    op_bits = part.operand_bits
                    if op_bits and len(op_bits) == 2:
                        op_msb, op_lsb = op_bits
                        shift = min(op_msb, op_lsb)
                        width = abs(op_msb - op_lsb) + 1
                        piece = (raw_value >> shift) & ((1 << width) - 1)
                    else:
                        piece = raw_value & 1
                    if len(instr_bits) == 2:
                        msb, lsb = instr_bits
                        word |= piece << lsb
                    else:
                        word |= piece << instr_bits[0]
            elif encoding.bits:
                # Simple contiguous encoding
                bits = encoding.bits
                if len(bits) == 2:
                    msb, lsb = bits
                    width = abs(msb - lsb) + 1
                    mask = (1 << width) - 1
                    word |= (raw_value & mask) << lsb
                else:
                    word |= (raw_value & 1) << bits[0]

        return word & 0xFFFFFFFF

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
