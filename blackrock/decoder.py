# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Decode a RISC-V instruction word into an InstructionInstance with operands filled from encoding.

Without external state (e.g. RegisterContext), GPR values and resolved names are not populated;
operand_values contain only what can be decoded from the instruction bits (register indices,
immediates, etc.).
"""

from typing import Any, Dict, Optional, Tuple

from instance import InstructionInstance
from instruction_loader import load_all_instructions
from models import FieldEncoding, InstructionDef


def _extract_bits(word: int, msb: int, lsb: int) -> int:
    """Extract bits [msb, lsb] from word (inclusive; RISC-V bit 0 is LSB)."""
    width = abs(msb - lsb) + 1
    return (word >> lsb) & ((1 << width) - 1)


def _sign_extend(value: int, width: int) -> int:
    """Sign-extend value from width bits to Python int."""
    sign_bit = 1 << (width - 1)
    if value & sign_bit:
        return value - (1 << width)
    return value


def _extract_field_from_word(word: int, encoding: FieldEncoding) -> Optional[int]:
    """Extract one field value from the instruction word using its encoding."""
    if encoding.parts:
        value = 0
        for part in encoding.parts:
            instr_bits = part.bits
            op_bits = part.operand_bits
            if len(instr_bits) == 2:
                msb, lsb = instr_bits
                piece = _extract_bits(word, msb, lsb)
            else:
                piece = _extract_bits(word, instr_bits[0], instr_bits[0])
            if op_bits is not None and len(op_bits) == 2:
                op_msb, op_lsb = op_bits
                shift = min(op_msb, op_lsb)
                value |= piece << shift
            else:
                value |= piece
        return value
    if encoding.bits is not None:
        bits = encoding.bits
        if len(bits) == 2:
            msb, lsb = bits
            return _extract_bits(word, msb, lsb)
        return _extract_bits(word, bits[0], bits[0])
    return None


def _immediate_decoded_value(raw: int, format_name: str, field_name: str) -> int:
    """Return the semantic immediate value (sign-extended / scaled per RISC-V)."""
    if format_name == "I":
        return _sign_extend(raw & 0xFFF, 12)
    if format_name == "S":
        return _sign_extend(raw & 0xFFF, 12)
    if format_name == "B":
        # 13-bit signed, scaled by 2
        return _sign_extend(raw & 0x1FFF, 13) * 2
    if format_name == "J":
        # 21-bit signed, scaled by 2
        return _sign_extend(raw & 0x1FFFFF, 21) * 2
    if format_name == "U":
        # 20-bit at [31:12], no sign extension (value as encoded)
        return raw & 0xFFFFF
    return raw


def _decode_operand_values(word: int, instruction: InstructionDef) -> Dict[str, Any]:
    """Extract all operand values from the instruction word."""
    values: Dict[str, Any] = {}
    fmt_name = instruction.format.name
    for name, encoding in instruction.fields.items():
        raw = _extract_field_from_word(word, encoding)
        if raw is None:
            continue
        if encoding.type == "immediate":
            values[name] = _immediate_decoded_value(raw, fmt_name, name)
        else:
            values[name] = raw
    return values


def _lookup_key(
    instruction: InstructionDef,
) -> Tuple[int, Optional[int], Optional[int]]:
    """(opcode, funct3, funct7) for table lookup; None where not in fixed_values."""
    fv = instruction.fixed_values
    opcode = fv.get("opcode")
    funct3 = fv.get("funct3")
    funct7 = fv.get("funct7")
    return (
        opcode if opcode is not None else 0,
        funct3 if funct3 is not None else None,
        funct7 if funct7 is not None else None,
    )


class Decoder:
    """Decodes 32-bit RISC-V instruction words into InstructionInstance using loaded InstructionDefs."""

    def __init__(
        self,
        instructions: Optional[Dict[str, InstructionDef]] = None,
    ) -> None:
        if instructions is None:
            instructions = load_all_instructions()
        self._instructions = instructions
        self._lookup: Dict[
            Tuple[int, Optional[int], Optional[int]], InstructionDef
        ] = {}
        for instr in self._instructions.values():
            key = _lookup_key(instr)
            self._lookup[key] = instr

    def decode(
        self,
        word: int,
        *,
        register_context: Optional[Any] = None,
        pc: Optional[int] = None,
    ) -> Optional[InstructionInstance]:
        """Decode a 32-bit instruction word into an InstructionInstance, or None if unknown.

        operand_values are filled from the encoding (rd, rs1, rs2, imm, etc.).
        Without register_context, GPR values are not populated (resolved_name/resolved_value
        remain None in OperandInfo). pc is stored on the instance if provided.
        """
        word = word & 0xFFFFFFFF
        opcode = _extract_bits(word, 6, 0)
        funct3 = _extract_bits(word, 14, 12)
        funct7 = _extract_bits(word, 31, 25)
        instr = (
            self._lookup.get((opcode, funct3, funct7))
            or self._lookup.get((opcode, funct3, None))
            or self._lookup.get((opcode, None, None))
        )
        if instr is None:
            return None
        operand_values = _decode_operand_values(word, instr)
        return InstructionInstance(
            instruction=instr,
            operand_values=operand_values,
            register_context=register_context,
            pc=pc,
        )


def decode(
    word: int,
    *,
    instructions: Optional[Dict[str, InstructionDef]] = None,
    register_context: Optional[Any] = None,
    pc: Optional[int] = None,
) -> Optional[InstructionInstance]:
    """Decode a 32-bit instruction word into an InstructionInstance.

    Convenience function that builds a Decoder with the given or default instructions.
    Returns None if the instruction is not recognized.
    """
    dec = Decoder(instructions=instructions)
    return dec.decode(word, register_context=register_context, pc=pc)
