# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Decode a RISC-V instruction word into an InstructionInstance with operands filled from encoding.

Without external state (e.g. RegisterContext), GPR values and resolved names are not populated;
operand_values contain only what can be decoded from the instruction bits (register indices,
immediates, etc.).
"""

from typing import Any, Dict, Optional, Tuple

from .instance import InstructionInstance
from .instruction_loader import load_all_instructions
from .models import FieldEncoding, InstructionDef


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
    """Decodes 32-bit RISC-V instruction words and assembly strings into InstructionInstance."""

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

    def from_opc(
        self,
        word: int,
        *,
        register_context: Optional[Any] = None,
        pc: Optional[int] = None,
    ) -> Optional[InstructionInstance]:
        """Decode a 32-bit instruction opcode into an InstructionInstance, or None if unknown.

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

    def from_asm(
        self,
        asm_str: str,
        *,
        register_context: Optional[Any] = None,
        pc: Optional[int] = None,
    ) -> InstructionInstance:
        """Parse an assembly string into an InstructionInstance.

        Args:
            asm_str: The assembly string to parse (e.g., 'addi x1, x2, 4')
            register_context: Optional register context
            pc: Optional program counter

        Raises:
            ValueError: If the instruction mnemonic is unknown or parse fails.
        """
        import re

        # Extract mnemonic from asm string
        stripped = asm_str.strip()
        if not stripped:
            raise ValueError("Empty or whitespace-only assembly string")
        asm_mnemonic = stripped.split()[0].lower()

        # Lookup instruction
        instruction = self._instructions.get(asm_mnemonic)
        if instruction is None:
            raise ValueError(f"Unknown instruction mnemonic: {asm_mnemonic}")

        fmt = instruction.format
        asm_formats = getattr(fmt, "asm_formats", None)
        if not asm_formats:
            raise ValueError(f"No asm_formats defined for format {fmt.name}")

        # Determine which format(s) to try
        # If instruction specifies asm_format, try that first, otherwise try all
        instruction_format = getattr(instruction, "asm_format", None)
        if instruction_format and instruction_format in asm_formats:
            # Try configured format first, then fall back to others
            format_order = [instruction_format] + [
                k for k in asm_formats.keys() if k != instruction_format
            ]
        else:
            # Try all formats in order
            format_order = list(asm_formats.keys())

        # Try each format entry until one matches
        for format_name in format_order:
            fmt_entry = asm_formats[format_name]
            operand_names = fmt_entry["operands"]
            offset_base = fmt_entry.get("offset_base", False)

            # Handle zero-operand instructions (e.g., ecall, ebreak, mret)
            if len(operand_names) == 0:
                # Match just the mnemonic with optional surrounding whitespace
                pattern = rf"^{re.escape(instruction.mnemonic)}$"
                m = re.match(pattern, asm_str.strip(), flags=re.IGNORECASE)
                if m:
                    return InstructionInstance(
                        instruction=instruction,
                        operand_values={},
                        register_context=register_context,
                        pc=pc,
                    )
                continue

            if offset_base and len(operand_names) >= 2:
                # Parse offset_base format: "mnemonic op1, offset(base)" or "mnemonic offset(base)"
                # Build regex to match
                if len(operand_names) > 2:
                    # Has operands before offset(base)
                    # e.g., "mnemonic rd, offset(base)"
                    num_prefix = len(operand_names) - 2
                    prefix_pattern = r",\s*".join([r"([^,\s()]+)"] * num_prefix)
                    pattern = rf"^{re.escape(instruction.mnemonic)}\s+{prefix_pattern}\s*,\s*([^,\s()]+)\(\s*([^)\s]+)\s*\)$"
                else:
                    # Just offset(base)
                    # e.g., "mnemonic offset(base)"
                    pattern = rf"^{re.escape(instruction.mnemonic)}\s+([^,\s()]+)\(\s*([^)\s]+)\s*\)$"

                m = re.match(pattern, asm_str.strip(), flags=re.IGNORECASE)
                if m:
                    values = list(m.groups())
                    # Map values to operand names
                    operand_values = {}
                    for i, op_name in enumerate(operand_names):
                        val = values[i]
                        op = instruction.operands.get(op_name)
                        if op and op.type == "register":
                            # Convert register name to index
                            if val.startswith("x") and val[1:].isdigit():
                                operand_values[op_name] = int(val[1:])
                            else:
                                # Try ABI name
                                from .instance import _reg_to_index

                                idx = _reg_to_index(val)
                                if idx is not None:
                                    operand_values[op_name] = idx
                                else:
                                    raise ValueError(f"Invalid register: {val}")
                        elif op and op.type == "immediate":
                            try:
                                operand_values[op_name] = int(val, 0)
                            except ValueError:
                                raise ValueError(f"Invalid immediate: {val}")
                        else:
                            operand_values[op_name] = val

                    return InstructionInstance(
                        instruction=instruction,
                        operand_values=operand_values,
                        register_context=register_context,
                        pc=pc,
                    )
            else:
                # Standard comma-separated format
                # Build regex to match operands
                pattern = (
                    rf"^{re.escape(instruction.mnemonic)}\s+"
                    + r",\s*".join([r"([^,\s()]+)"] * len(operand_names))
                    + r"$"
                )

                m = re.match(pattern, asm_str.strip(), flags=re.IGNORECASE)
                if m:
                    values = list(m.groups())
                    # Map values to operand names
                    operand_values = {}
                    for i, op_name in enumerate(operand_names):
                        val = values[i]
                        op = instruction.operands.get(op_name)
                        if op and op.type == "register":
                            # Convert register name to index
                            if val.startswith("x") and val[1:].isdigit():
                                operand_values[op_name] = int(val[1:])
                            else:
                                # Try ABI name
                                from .instance import _reg_to_index

                                idx = _reg_to_index(val)
                                if idx is not None:
                                    operand_values[op_name] = idx
                                else:
                                    raise ValueError(f"Invalid register: {val}")
                        elif op and op.type == "immediate":
                            try:
                                operand_values[op_name] = int(val, 0)
                            except ValueError:
                                raise ValueError(f"Invalid immediate: {val}")
                        else:
                            operand_values[op_name] = val

                    return InstructionInstance(
                        instruction=instruction,
                        operand_values=operand_values,
                        register_context=register_context,
                        pc=pc,
                    )

        raise ValueError(
            f"Could not parse asm string '{asm_str}' for instruction {instruction.mnemonic}"
        )
