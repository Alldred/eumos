import os
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pykwalify.core import Core

@dataclass
class FieldPart:
    bits: Any

@dataclass
class FieldDef:
    name: str
    type: str
    bits: Any = None
    parts: Optional[List[FieldPart]] = None

@dataclass
class FormatDef:
    name: str
    fullname: str
    asm_format: str
    fields: List[FieldDef]
    description: str

@dataclass
class Operand:
    name: str
    type: str
    size: int
    data: Any = None

@dataclass
class InstructionDef:
    name: str
    mnemonic: str
    fixed_values: Dict[str, Any] = field(default_factory=dict)
    imm: Optional[Any] = None
    format: FormatDef = None
    description: str = ""
    inputs: List[str] = field(default_factory=list)
    operands: Dict[str, Operand] = field(default_factory=dict)

def validate_yaml_schema(yaml_path, schema_path):
    core = Core(source_file=yaml_path, schema_files=[schema_path])
    core.validate()

def load_yaml(filepath):
    import yaml
    with open(filepath, "r") as f:
        return yaml.safe_load(f)

def load_format(format_dir, format_name):
    path = os.path.join(format_dir, format_name + '.yml')
    schema_path = os.path.join(os.path.dirname(__file__), 'format_schema.yaml')
    validate_yaml_schema(path, schema_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Format file not found: {path}")
    data = load_yaml(path)
    fields = []
    for fld in data.get("fields", []):
        if 'parts' in fld:
            parts = [FieldPart(**p) for p in fld['parts']]
            fields.append(FieldDef(name=fld['name'], type=fld['type'], parts=parts))
        else:
            fields.append(FieldDef(**fld))
    return FormatDef(
        name=data["name"],
        fullname=data.get("fullname", ""),
        asm_format=data.get("asm_format", ""),
        fields=fields,
        description=data.get("description", "")
    )

def load_instruction(instr_path, format_dir):
    schema_path = os.path.join(os.path.dirname(__file__), 'instruction_schema.yaml')
    validate_yaml_schema(instr_path, schema_path)
    data = load_yaml(instr_path)
    fmt = load_format(format_dir, data["format"])
    fixed_keys = ["opcode", "funct3", "funct7"]
    fixed_values = {}
    if 'fixed_values' in data:
        fixed_values = {k: data['fixed_values'][k] for k in fixed_keys if k in data['fixed_values']}
    operands = {}
    for field in fmt.fields:
        # Handle split fields (parts)
        if hasattr(field, 'parts') and field.parts:
            # For split fields, sum all bits from all parts
            total_bits = 0
            for part in field.parts:
                bits = part.bits
                if isinstance(bits, list):
                    # bits: [msb, lsb]
                    if len(bits) == 2:
                        msb, lsb = bits
                        total_bits += abs(msb - lsb) + 1
                    else:
                        # single bit
                        total_bits += 1
            operands[field.name] = Operand(
                name=field.name,
                type=field.type,
                size=total_bits,
                data=fixed_values.get(field.name)
            )
        else:
            if isinstance(field.bits, list):
                all_bits = []
                for b in field.bits:
                    if isinstance(b, list):
                        msb, lsb = b[0], b[1]
                        all_bits.extend(range(lsb, msb+1))
                    elif isinstance(b, str) and ":" in b:
                        msb, lsb = map(int, b.split(":"))
                        all_bits.extend(range(lsb, msb+1))
                    elif isinstance(b, int):
                        all_bits.append(b)
                size = len(all_bits) if all_bits else None
            elif isinstance(field.bits, str) and ":" in field.bits:
                msb, lsb = map(int, field.bits.split(":"))
                size = abs(msb - lsb) + 1
            else:
                try:
                    size = 1
                except Exception:
                    size = None
            data_val = fixed_values.get(field.name)
            operands[field.name] = Operand(
                name=field.name,
                type=field.type,
                size=size,
                data=data_val
            )
    return InstructionDef(
        name=data["name"],
        mnemonic=data["mnemonic"],
        fixed_values=fixed_values,
        imm=data.get("imm"),
        format=fmt,
        description=data.get("description", ""),
        inputs=data.get("inputs", []),
        operands=operands
    )

def load_all_instructions(
    instr_root: Optional[str] = None,
    format_dir: Optional[str] = None
):
    if instr_root is None:
        instr_root = "yaml/rv64/instructions"
    if format_dir is None:
        format_dir = "yaml/rv64/formats"
    instructions = {}
    for root, _, files in os.walk(instr_root):
        for file in files:
            if file.endswith(".yml") or file.endswith(".yaml"):
                instr_path = os.path.join(root, file)
                instr = load_instruction(instr_path, format_dir)
                instructions[instr.mnemonic] = instr
    return instructions


# Example usage:
# instrs = load_all_instructions()
# print(instrs[0])

if __name__ == "__main__":
    # Load all instructions and print the first one
    instrs = load_all_instructions()
    if instrs:
        first_instr = next(iter(instrs.values()))
        for k, v in first_instr.__dict__.items():
            if isinstance(v, dict):
                print(f"{k}: {{key: str(item) for key, item in v.items()}}")
            else:
                print(f"{k}: {v}")
    else:
        print("No instructions found.")