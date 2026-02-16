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

    @property
    def memory_access_width(self) -> Optional[int]:
        """Alias for access_width (bits)."""
        return self.access_width


@dataclass
class GPRDef:
    """ISA definition for one general-purpose register: index, ABI name, reset value, and access."""

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
