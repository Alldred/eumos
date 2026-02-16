# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Encode instruction operand values into a 32-bit RISC-V opcode."""

from typing import Any, Dict

from .models import FieldEncoding, InstructionDef


def _insert_bits(word: int, value: int, msb: int, lsb: int) -> int:
    """Insert value into word at bits [msb:lsb] inclusive."""
    width = abs(msb - lsb) + 1
    mask = (1 << width) - 1
    masked = (value & mask) << lsb
    return (word & ~(mask << lsb)) | masked


def _immediate_to_raw(value: int, format_name: str) -> int:
    """Convert semantic immediate to raw encoded bits (before split encoding)."""
    if format_name in ("I", "S"):
        return value & 0xFFF
    if format_name == "B":
        # value is byte offset (multiple of 2); 13-bit signed
        return (value >> 1) & 0x1FFF
    if format_name == "J":
        # value is byte offset (multiple of 2); 21-bit signed
        return (value >> 1) & 0x1FFFFF
    if format_name == "U":
        return value & 0xFFFFF
    return value & 0xFFF


def _encode_field_value(value: Any, encoding: FieldEncoding, format_name: str) -> int:
    """Encode one field value into raw bits for insertion."""
    if encoding.type == "immediate":
        val = int(value)
        if format_name == "B":
            if val % 2 != 0:
                raise ValueError(
                    f"B-type immediate offset {val} is not 2-byte aligned and cannot be encoded"
                )
        elif format_name == "J":
            if val % 2 != 0:
                raise ValueError(
                    f"J-type immediate offset {val} is not 2-byte aligned and cannot be encoded"
                )
        raw = _immediate_to_raw(val, format_name)
    elif encoding.type == "register":
        if not isinstance(value, int):
            raise ValueError(
                f"Register operand must be int, got {type(value).__name__}"
            )
        if not 0 <= value <= 31:
            raise ValueError(f"Register index out of range 0..31: {value}")
        raw = value
    else:
        raw = int(value)

    if encoding.parts:
        # Split fields (S, B, J): caller handles placement per part
        return raw
    if encoding.bits is not None:
        bits = encoding.bits
        if len(bits) == 2:
            msb, lsb = bits
            width = abs(msb - lsb) + 1
            return raw & ((1 << width) - 1)
        return raw & 1
    return raw


def _encode_parts(word: int, raw_value: int, encoding: FieldEncoding) -> int:
    """Insert split immediate into word per encoding.parts."""
    if not encoding.parts:
        return word
    for part in encoding.parts:
        instr_bits = part.bits
        op_bits = part.operand_bits
        if op_bits is not None and len(op_bits) == 2:
            op_msb, op_lsb = op_bits
            shift = min(op_msb, op_lsb)
            piece_width = abs(op_msb - op_lsb) + 1
            piece = (raw_value >> shift) & ((1 << piece_width) - 1)
        else:
            piece = raw_value & 1
        if len(instr_bits) == 2:
            msb, lsb = instr_bits
            word = _insert_bits(word, piece, msb, lsb)
        else:
            word = _insert_bits(word, piece, instr_bits[0], instr_bits[0])
    return word


def encode_instruction(
    instruction: InstructionDef, operand_values: Dict[str, Any]
) -> int:
    """Encode an instruction with given operand values to a 32-bit opcode."""
    word = 0
    fmt_name = instruction.format.name if instruction.format else "I"
    fv = instruction.fixed_values or {}

    for name, encoding in instruction.fields.items():
        if name in fv:
            val = fv[name]
        else:
            val = operand_values.get(name)
        if val is None:
            continue

        if encoding.parts:
            raw = _encode_field_value(val, encoding, fmt_name)
            word = _encode_parts(word, raw, encoding)
        elif encoding.bits is not None:
            raw = _encode_field_value(val, encoding, fmt_name)
            bits = encoding.bits
            if len(bits) == 2:
                msb, lsb = bits
                word = _insert_bits(word, raw, msb, lsb)
            else:
                word = _insert_bits(word, raw, bits[0], bits[0])

    return word & 0xFFFF_FFFF
