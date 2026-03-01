# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Load RISC-V instruction YAML into Python objects, recursively."""

import os
import re
import warnings
from typing import Any, Dict, List, Set

from .format_loader import load_all_formats
from .models import FieldEncoding, FormatDef, Instruction, Operand
from .validation import load_yaml, validate_yaml_schema

# Optional: known groups for allowlist validation (warn on unknown).
_GROUP_FORMAT = re.compile(r"^[a-z][a-z0-9]*(/[a-z][a-z0-9]*)*$")
_KNOWN_GROUPS: Set[str] = {
    "memory/load",
    "memory/store",
    "branch/conditional",
    "branch/jump",
    "alu",
    "alu/arith",
    "alu/logical",
    "alu/constant",
    "system/csr",
    "system/call",
    "system/return",
    "system/ordering",
    "float",
    "float/load",
    "float/store",
    "compressed",
}

_INSTR_SCHEMA = os.path.join(
    os.path.dirname(__file__), "arch", "schemas", "instruction_schema.yaml"
)
_INSTR_ROOT = os.path.join(os.path.dirname(__file__), "arch", "rv64", "instructions")


def _immediate_size_for_format(format_name: str) -> int:
    """Return immediate width in bits for the format."""
    if format_name in ("I", "S", "B"):
        return 12
    if format_name == "U":
        return 20
    if format_name == "J":
        return 21
    return 12


def _build_operands_and_fields(raw: dict, format_obj) -> tuple:
    """Build operands and fields dicts from format and instruction inputs."""
    inputs = raw.get("inputs") or []
    fmt_name = format_obj.name
    imm_size = _immediate_size_for_format(fmt_name)
    operands: Dict[str, Operand] = {}
    fields: Dict[str, FieldEncoding] = {}
    for f in format_obj.fields:
        name, typ = f.name, f.type
        size = 5 if typ == "register" else (imm_size if typ == "immediate" else 0)
        enc = FieldEncoding(name=name, type=typ, bits=f.bits, parts=f.parts)
        fields[name] = enc
        if name in inputs or typ in ("register", "immediate"):
            operands[name] = Operand(name=name, type=typ, size=size, data=None)
    return operands, fields


def _normalize_operand_aliases(
    file_path: str, raw_aliases: dict | None, operands: Dict[str, Operand]
) -> Dict[str, List[str]]:
    """Validate and normalize operand alias mapping from YAML."""
    if raw_aliases is None:
        return {}
    if not isinstance(raw_aliases, dict):
        raise ValueError(
            f"{file_path}: 'operand_aliases' must be a mapping of canonical operand -> list of aliases."
        )
    normalized: Dict[str, List[str]] = {}
    alias_owner: Dict[str, str] = {}
    for canonical, aliases in raw_aliases.items():
        if not isinstance(canonical, str):
            raise ValueError(
                f"{file_path}: operand_aliases keys must be strings, got {type(canonical).__name__}."
            )
        canonical_name = canonical.strip()
        operand = operands.get(canonical_name)
        if operand is None:
            raise ValueError(
                f"{file_path}: operand_aliases key {canonical_name!r} is not a defined operand."
            )
        if operand.type != "immediate":
            raise ValueError(
                f"{file_path}: operand_aliases currently supports immediate operands only; "
                f"{canonical_name!r} is type {operand.type!r}."
            )
        if not isinstance(aliases, list) or not aliases:
            raise ValueError(
                f"{file_path}: operand_aliases[{canonical_name!r}] must be a non-empty list of strings."
            )
        clean_aliases: List[str] = []
        seen = set()
        for alias in aliases:
            if not isinstance(alias, str):
                raise ValueError(
                    f"{file_path}: operand_aliases[{canonical_name!r}] entries must be strings."
                )
            alias_name = alias.strip()
            if not alias_name:
                raise ValueError(
                    f"{file_path}: operand_aliases[{canonical_name!r}] cannot contain empty alias."
                )
            if alias_name == canonical_name:
                raise ValueError(
                    f"{file_path}: operand_aliases[{canonical_name!r}] cannot repeat canonical name."
                )
            if alias_name in operands:
                raise ValueError(
                    f"{file_path}: alias {alias_name!r} conflicts with an existing operand name."
                )
            if alias_name in seen:
                continue
            owner = alias_owner.get(alias_name)
            if owner is not None and owner != canonical_name:
                raise ValueError(
                    f"{file_path}: alias {alias_name!r} is mapped to multiple operands "
                    f"({owner!r}, {canonical_name!r})."
                )
            alias_owner[alias_name] = canonical_name
            seen.add(alias_name)
            clean_aliases.append(alias_name)
        normalized[canonical_name] = clean_aliases
    return normalized


def _normalize_immediate_encoding(
    file_path: str, raw_encoding: dict | None, operands: Dict[str, Operand]
) -> Dict[str, Dict[str, Any]]:
    """Validate and normalize immediate encoding metadata from YAML."""
    if raw_encoding is None:
        return {}
    if not isinstance(raw_encoding, dict):
        raise ValueError(
            f"{file_path}: 'immediate_encoding' must be a mapping of operand -> metadata."
        )
    normalized: Dict[str, Dict[str, Any]] = {}
    for canonical, spec in raw_encoding.items():
        if not isinstance(canonical, str):
            raise ValueError(
                f"{file_path}: immediate_encoding keys must be strings, got {type(canonical).__name__}."
            )
        canonical_name = canonical.strip()
        operand = operands.get(canonical_name)
        if operand is None:
            raise ValueError(
                f"{file_path}: immediate_encoding key {canonical_name!r} is not a defined operand."
            )
        if operand.type != "immediate":
            raise ValueError(
                f"{file_path}: immediate_encoding currently supports immediate operands only; "
                f"{canonical_name!r} is type {operand.type!r}."
            )
        if not isinstance(spec, dict):
            raise ValueError(
                f"{file_path}: immediate_encoding[{canonical_name!r}] must be a mapping."
            )
        mode = spec.get("mode")
        if mode != "shift":
            raise ValueError(
                f"{file_path}: immediate_encoding[{canonical_name!r}].mode must be 'shift'."
            )
        width = spec.get("width")
        if not isinstance(width, int) or width <= 0:
            raise ValueError(
                f"{file_path}: immediate_encoding[{canonical_name!r}].width must be a positive int."
            )
        prefix = spec.get("prefix", 0)
        if not isinstance(prefix, int) or prefix < 0:
            raise ValueError(
                f"{file_path}: immediate_encoding[{canonical_name!r}].prefix must be a non-negative int."
            )
        normalized[canonical_name] = {"mode": mode, "width": width, "prefix": prefix}
    return normalized


def _load_instruction(
    file_path: str, schema_path: str, formats: Dict[str, FormatDef]
) -> Instruction:
    """Load and validate a single instruction YAML file. Expects exactly one instruction per file."""
    validate_yaml_schema(file_path, schema_path)
    data = load_yaml(file_path)
    instructions = data.get("instructions", [data])
    if len(instructions) != 1:
        raise ValueError(
            f"Expected exactly one instruction in {file_path}, found {len(instructions)}."
        )
    raw = dict(instructions[0])
    format_name = raw.get("format")
    if not isinstance(format_name, str):
        raise ValueError(
            f"{file_path}: 'format' must be a string, got {type(format_name).__name__}."
        )
    if format_name not in formats:
        raise ValueError(
            f"{file_path}: format '{format_name}' not found in formats (known: {sorted(formats)})."
        )
    format_obj = formats[format_name]
    operands, fields = _build_operands_and_fields(raw, format_obj)
    raw["operand_aliases"] = _normalize_operand_aliases(
        file_path, raw.get("operand_aliases"), operands
    )
    raw["operand_alias_lookup"] = {
        alias: canonical
        for canonical, aliases in raw["operand_aliases"].items()
        for alias in aliases
    }
    raw["immediate_encoding"] = _normalize_immediate_encoding(
        file_path, raw.get("immediate_encoding"), operands
    )
    raw["format"] = format_obj
    raw["operands"] = operands
    raw["fields"] = fields
    asm_format = raw.get("asm_format")
    asm_formats = getattr(format_obj, "asm_formats", None) or {}
    if asm_format not in asm_formats:
        raise ValueError(
            f"{file_path}: asm_format '{asm_format}' not in format {format_name} asm_formats {list(asm_formats)}"
        )
    # Expose fixed imm as top-level imm when present (e.g. ECALL has imm in fixed_values only)
    if "imm" not in raw and raw.get("fixed_values"):
        fv_imm = raw["fixed_values"].get("imm")
        if fv_imm is not None:
            raw["imm"] = fv_imm

    # Groups: required, non-empty; normalize (strip, lowercase); optional format and allowlist
    groups_raw = raw.get("groups")
    if groups_raw is None:
        raise ValueError(f"{file_path}: missing required 'groups'.")
    if not isinstance(groups_raw, list) or len(groups_raw) == 0:
        raise ValueError(f"{file_path}: 'groups' must be a non-empty list.")
    normalized = []
    for g in groups_raw:
        if not isinstance(g, str):
            raise ValueError(
                f"{file_path}: each 'groups' entry must be a string, got {type(g).__name__}."
            )
        s = g.strip().lower()
        if not s:
            raise ValueError(f"{file_path}: empty group string in 'groups'.")
        if not _GROUP_FORMAT.match(s):
            raise ValueError(
                f"{file_path}: group {g!r} does not match format (e.g. 'memory/load', 'alu')."
            )
        if s not in _KNOWN_GROUPS:
            warnings.warn(
                f"{file_path}: unknown group {s!r} (not in known-groups allowlist).",
                UserWarning,
                stacklevel=2,
            )
        normalized.append(s)
    raw["groups"] = normalized

    return Instruction(**raw)


def load_all_instructions() -> Dict[str, Instruction]:
    """Recursively load all instruction YAML files from built-in arch; returns dict mnemonic -> Instruction."""
    formats = load_all_formats()
    instr_root = os.path.abspath(_INSTR_ROOT)
    schema_path = _INSTR_SCHEMA
    result: Dict[str, Instruction] = {}
    for dirpath, _, files in os.walk(instr_root):
        for file in files:
            if file.endswith(".yml") or file.endswith(".yaml"):
                file_path = os.path.join(dirpath, file)
                instr_obj = _load_instruction(file_path, schema_path, formats)
                result[instr_obj.mnemonic] = instr_obj
    return result


def instructions_by_group(
    instructions: Dict[str, Instruction], group: str
) -> Dict[str, Instruction]:
    """Return instructions that belong to the given group (exact or path prefix match)."""
    g = group.strip().lower()
    return {
        mnemonic: instr for mnemonic, instr in instructions.items() if instr.in_group(g)
    }


def instruction_groups(instructions: Dict[str, Instruction]) -> List[str]:
    """Return all distinct groups from the given instructions (sorted)."""
    out: Set[str] = set()
    for instr in instructions.values():
        out.update(instr.groups)
    return sorted(out)
