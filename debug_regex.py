#!/usr/bin/env python3
import re

pattern = "{mnemonic} {rd:reg}, {rs1:reg}, {imm:imm}"
asm_str = 'addi x1, x2, 4'
instruction_mnemonic = 'addi'

# Step 1: Mark literal parens with placeholders
regex = pattern.replace("(", "<<<LPAREN>>>")
regex = regex.replace(")", "<<<RPAREN>>>")
print(f"After paren placeholder: {regex}")

# Step 2: Replace mnemonic
regex = regex.replace("{mnemonic}", re.escape(instruction_mnemonic))
print(f"After mnemonic replace: {regex}")

# Step 3: Replace {operand:type} with named groups
def group_repl(m):
    name = m.group(1)
    return f"(?P<{name}>[^,\\\\s()]+)"

regex = re.sub(r"{([a-zA-Z0-9_]+)(:[^}]*)?}", group_repl, regex)
print(f"After group replace: {regex}")

# Step 4: Replace commas and spaces
regex = regex.replace(",", r"\s*,\s*")
print(f"After comma replace: {regex}")

regex = regex.replace(" ", r"\s+")
print(f"After space replace: {regex}")

# Step 5: Replace placeholders with escaped parens
regex = regex.replace("<<<LPAREN>>>", r"\(")
regex = regex.replace("<<<RPAREN>>>", r"\)")
print(f"After paren replace: {regex}")

print(f"\nFinal regex: ^{regex}$")
print(f"Test string: {asm_str.strip()}")

m = re.match(rf"^{regex}$", asm_str.strip())
if m:
    print(f"Match: {m.groupdict()}")
else:
    print("No match")
