# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Data structures for RISC-V instruction and format specs (ISA only; no file I/O)."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class FieldPart:
    """One piece of a split field: bit range in the opcode and optional operand bit range."""

    bits: Any  # bits in the opcode
    operand_bits: Any = None  # bits in the operand (new field)


@dataclass
class FieldDef:
    """Format field: name, type, and either bits or parts (for split fields like imm in S/B)."""

    name: str
    type: str
    bits: Any = None
    parts: Optional[List[FieldPart]] = None


@dataclass
class FormatDef:
    """Instruction format (R, I, S, B, etc.): name, asm_formats (dict mapping format names to specs), and list of fields."""

    name: str
    fullname: str
    asm_formats: Dict[
        str, Dict[str, Any]
    ]  # e.g., {"default": {"operands": [...]}, "offset_base": {...}}
    fields: List[FieldDef]
    description: str


@dataclass
class ExceptionCauseDef:
    """RISC-V trap/exception cause: code, human name, and identifier."""

    code: int
    name: str
    identifier: str  # UPPERCASE_SNAKE for logging


@dataclass
class Operand:
    """Operand spec: name, type (register/immediate/etc), size in bits, optional fixed data."""

    name: str
    type: str
    size: int
    data: Any = None


@dataclass
class FieldEncoding:
    """Encoding of one field: name, type, and either bits or parts for split fields."""

    name: str
    type: str
    bits: Any = None
    parts: Optional[List[FieldPart]] = None


@dataclass
class InstructionDef:
    """
    ISA definition for one instruction: mnemonic, format, operands, fields, fixed_values, extension.

    - operands: The logical inputs to the instruction (registers, immediates, etc.).
      These represent what the instruction uses semantically.
    - fields: The bit-level encoding details for those operands and other instruction components.
      Fields describe how each operand (and other values like opcode) are represented in the binary encoding.
    """

    name: str
    mnemonic: str
    fixed_values: Dict[str, Any] = field(default_factory=dict)
    imm: Optional[Any] = None
    format: FormatDef = None
    description: str = ""
    inputs: List[str] = field(default_factory=list)
    operands: Dict[str, Operand] = field(default_factory=dict)
    fields: Dict[str, FieldEncoding] = field(default_factory=dict)
    extension: str = ""
    asm_format: Optional[str] = None
    source_file: Optional[str] = None
    access_width: Optional[int] = None  # bits, for load/store only
    exceptions: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)

    def in_group(self, group: str) -> bool:
        """True if this instruction belongs to the given group (exact or path prefix)."""
        g = group.strip().lower()
        for tag in self.groups:
            tag = tag.strip().lower()
            if tag == g or tag.startswith(g + "/"):
                return True
        return False

    def uses_rounding_mode_operand(self) -> bool:
        """True if this instruction encodes rounding mode (rm) in funct3; operand_values should include 'rm'."""
        if self.extension not in ("F", "D"):
            return False
        if "funct3" in (self.fixed_values or {}):
            return False
        fmt_name = getattr(self.format, "name", None) if self.format else None
        return fmt_name in ("R", "R4")

    @property
    def memory_access_width(self) -> Optional[int]:
        """Alias for access_width (bits)."""
        return self.access_width

    def _register_operand_role(self, op_name: str) -> Optional[Tuple[bool, bool]]:
        """Return (is_gpr, is_dest) for register operand op_name, or None if not a register.
        (True, True) = GPR dest, (True, False) = GPR source, (False, True) = FPR dest, (False, False) = FPR source.
        """
        op = self.operands.get(op_name)
        if not op or op.type != "register":
            return None
        ext = self.extension
        mnem = self.mnemonic.lower()
        is_load = self.in_group("float/load")
        is_store = self.in_group("float/store")

        if ext not in ("F", "D"):
            # Integer instruction: all register operands are GPR
            is_dest = op_name == "rd"
            return (True, is_dest)

        # F/D: classify by op_name and instruction semantics
        if is_load:
            if op_name == "rd":
                return (False, True)  # FPR dest
            if op_name == "rs1":
                return (True, False)  # GPR source (base)
            return None
        if is_store:
            if op_name == "rs2":
                return (False, False)  # FPR source
            if op_name == "rs1":
                return (True, False)  # GPR source (base)
            return None

        # rd is GPR dest for: compare, fclass, fcvt float->int, fmv.x
        rd_is_gpr = (
            mnem.startswith("feq.")
            or mnem.startswith("flt.")
            or mnem.startswith("fle.")
            or mnem.startswith("fclass.")
            or mnem
            in (
                "fcvt.w.s",
                "fcvt.wu.s",
                "fcvt.w.d",
                "fcvt.wu.d",
                "fcvt.l.s",
                "fcvt.lu.s",
                "fcvt.l.d",
                "fcvt.lu.d",
            )
            or mnem in ("fmv.x.w", "fmv.x.d")
        )
        # rs1 is GPR source for: fcvt int->float, fmv.w.x, fmv.d.x
        rs1_is_gpr = mnem in (
            "fcvt.s.w",
            "fcvt.s.wu",
            "fcvt.s.l",
            "fcvt.s.lu",
            "fcvt.d.w",
            "fcvt.d.wu",
            "fcvt.d.l",
            "fcvt.d.lu",
        ) or mnem in ("fmv.w.x", "fmv.d.x")

        if op_name == "rd":
            return (rd_is_gpr, True)
        if op_name == "rs1":
            return (rs1_is_gpr, False)
        if op_name in ("rs2", "rs3"):
            # Fixed rs2/rs3 (e.g. FCVT.W.S rs2=0, FMV.X.W rs2=0) are encoding-only, not real sources
            if op_name in self.fixed_values:
                return None
            return (False, False)  # FPR source
        return (False, False)

    def is_operand_fpr(self, op_name: str) -> bool:
        """True if the register operand op_name is an FPR (use 'f' prefix in asm / parse as f0-f31)."""
        role = self._register_operand_role(op_name)
        return role is not None and not role[0]  # register and not GPR => FPR

    def gpr_source_operands(self) -> List[str]:
        """Operand names that are GPR (integer) sources. Empty if not applicable."""
        out: List[str] = []
        for name in self.operands:
            role = self._register_operand_role(name)
            if role and role[0] and not role[1]:  # GPR, source
                out.append(name)
        return out

    def gpr_dest_operands(self) -> List[str]:
        """Operand names that are GPR (integer) destinations. Empty if not applicable."""
        out: List[str] = []
        for name in self.operands:
            role = self._register_operand_role(name)
            if role and role[0] and role[1]:  # GPR, dest
                out.append(name)
        return out

    def fpr_source_operands(self) -> List[str]:
        """Operand names that are FPR (float) sources. Empty if not applicable."""
        out: List[str] = []
        for name in self.operands:
            role = self._register_operand_role(name)
            if role and not role[0] and not role[1]:  # FPR, source
                out.append(name)
        return out

    def fpr_dest_operands(self) -> List[str]:
        """Operand names that are FPR (float) destinations. Empty if not applicable."""
        out: List[str] = []
        for name in self.operands:
            role = self._register_operand_role(name)
            if role and not role[0] and role[1]:  # FPR, dest
                out.append(name)
        return out

    def operand_register_bank(self, op_name: str) -> Optional[str]:
        """Return the register bank for operand op_name: 'gpr', 'fpr', or None if not a register."""
        role = self._register_operand_role(op_name)
        if role is None:
            return None
        return "gpr" if role[0] else "fpr"

    def operand_banks(self) -> Dict[str, str]:
        """Return a dict of operand name -> 'gpr' or 'fpr' for all register operands."""
        out: Dict[str, str] = {}
        for name in self.operands:
            bank = self.operand_register_bank(name)
            if bank is not None:
                out[name] = bank
        return out


@dataclass
class GPRDef:
    """ISA definition for one general-purpose register: index, ABI name, reset value, and access."""

    index: int
    abi_name: str
    reset_value: int
    access: str
    source_file: Optional[str] = None


@dataclass
class FPRDef:
    """ISA definition for one floating-point register: index, ABI name, reset value, and access."""

    index: int
    abi_name: str
    reset_value: int
    access: str
    source_file: Optional[str] = None


@dataclass
class CSRFieldDef:
    """One named field within a CSR: bit range, optional description, reset value, and access override."""

    name: str
    bits: Union[int, Tuple[int, int]]  # single bit or (high, low) inclusive
    description: str = ""
    reset_value: Optional[int] = None
    access: Optional[str] = None  # overrides CSR-level access when set


@dataclass
class CSRDef:
    """ISA definition for one control and status register: name, address, and optional metadata."""

    name: str
    address: int
    description: str = ""
    privilege: Optional[str] = None
    access: Optional[str] = None
    width: Optional[int] = None
    extension: Optional[str] = None
    reset_value: Optional[int] = None
    fields: Optional[Dict[str, CSRFieldDef]] = None
    source_file: Optional[str] = None


# Aliases used by loaders
CSR = CSRDef
Format = FormatDef
Instruction = InstructionDef
GPR = GPRDef
FPR = FPRDef
