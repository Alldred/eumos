#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Example demonstrating assembly parsing, encoding, and decoding with eumos."""

from eumos import instruction_loader
from eumos.decoder import Decoder
from eumos.instance import InstructionInstance


def main():
    print("\n=== Eumos Assembly & Encoding Example ===\n")
    
    # Load instruction definitions and create decoder
    instructions = instruction_loader.load_all_instructions()
    decoder = Decoder(instructions)
    
    # Example 1: Parse assembly with Decoder.from_asm()
    print("1. Parse assembly string with decoder.from_asm():")
    asm1 = "addi x1, x2, 4"
    instance1 = decoder.from_asm(asm1)
    print(f"   Input:  {asm1}")
    print(f"   Parsed: {instance1.instruction.mnemonic} with operands {instance1.operand_values}")
    print(f"   Output asm: {instance1.to_asm()}")
    print(f"   Output opc: 0x{instance1.to_opc():08x}")
    
    # Example 2: Decode opcode with decoder.from_opc()
    print("\n2. Decode opcode with decoder.from_opc():")
    opcode2 = 0x005211b3  # sll x3, x4, x5
    instance2 = decoder.from_opc(opcode2)
    print(f"   Opcode: 0x{opcode2:08x}")
    print(f"   → {instance2.to_asm()}")
    print(f"   Instruction: {instance2.instruction.name}")
    
    # Example 3: Full round-trip (asm → opcode → asm)
    print("\n3. Full round-trip (asm → opcode → asm):")
    asm3 = "sd x6, 8(x7)"
    print(f"   Original: {asm3}")
    instance3 = decoder.from_asm(asm3)
    opcode3 = instance3.to_opc()
    print(f"   Encoded:  0x{opcode3:08x}")
    decoded3 = decoder.from_opc(opcode3)
    print(f"   Decoded:  {decoded3.to_asm()}")
    print(f"   Match: {asm3 == decoded3.to_asm()}")
    
    # Example 4: Programmatic instruction creation
    print("\n4. Programmatic instruction creation:")
    jalr_instr = instructions["jalr"]
    instance4 = InstructionInstance(
        instruction=jalr_instr,
        operand_values={"rd": 0, "rs1": 2, "imm": 0}
    )
    print(f"   Created: jalr(rd=0, rs1=2, imm=0)")
    print(f"   Assembly: {instance4.to_asm()}")
    print(f"   Opcode:   0x{instance4.to_opc():08x}")
    
    print("\n=== Complete ===\n")


if __name__ == "__main__":
    main()
