# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Data structures for RISC-V instruction and format specs (ISA only; no file I/O)."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
    """Instruction format (R, I, S, B, etc.): name, asm_format string, and list of fields."""

    name: str
    fullname: str
    asm_format: str
    fields: List[FieldDef]
    description: str


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
    """ISA definition for one instruction: mnemonic, format, operands, fields, fixed_values, extension."""

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
    source_file: Optional[str] = None


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
    source_file: Optional[str] = None
