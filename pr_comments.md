author:	copilot-pull-request-reviewer
association:	none
edited:	false
status:	commented
--
## Pull request overview

This PR refactors how instruction assembly formats are represented (moving from a single `asm_format` string to multiple named `asm_formats`) and expands the decoding/encoding surface area by adding assembly parsing (`Decoder.from_asm`) plus instance serialization (`InstructionInstance.to_asm` / `to_opc`).

**Changes:**
- Replace `Format.asm_format` with `Format.asm_formats` and add per-instruction `asm_format` selection (e.g. load/jalr use `offset_base`).
- Add `Decoder.from_opc()` and `Decoder.from_asm()` to decode opcodes and parse assembly strings.
- Add opcode/assembly round-trip support via `InstructionInstance.to_asm()` and `InstructionInstance.to_opc()`, plus new tests/examples/docs.

### Reviewed changes

Copilot reviewed 29 out of 29 changed files in this pull request and generated 15 comments.

<details>
<summary>Show a summary per file</summary>

| File | Description |
| ---- | ----------- |
| tests/test_isa.py | Updates decoder call site to `from_opc`. |
| tests/test_format_loader.py | Updates expectations for `asm_formats` structure. |
| tests/test_decoder_api.py | Adds tests for `from_opc`/`from_asm` API. |
| tests/test_decoder.py | Migrates tests from `decode()` to `from_opc()` and updates API usage. |
| tests/test_asm_roundtrip.py | Adds asm ⇄ instance ⇄ opcode round-trip tests. |
| tests/test_asm_auto_detect.py | Adds tests for `from_asm` auto-detection behavior. |
| example/asm_encoding_example.py | Adds an example script demonstrating asm parsing and encoding. |
| eumos/models.py | Updates data model: `FormatDef.asm_formats` and adds `InstructionDef.asm_format`. |
| eumos/instance.py | Adds `InstructionInstance.to_asm()`/`to_opc()` plus compatibility alias `asm()`. |
| eumos/format_loader.py | Minor formatting change while loading formats. |
| eumos/decoder.py | Introduces `Decoder.from_opc()` and `Decoder.from_asm()` parsing logic; removes old convenience `decode()` function. |
| eumos/arch/schemas/instruction_schema.yaml | Allows optional `asm_format` in instruction YAML. |
| eumos/arch/schemas/format_schema.yaml | Updates schema to require `asm_formats` map (but currently missing license header). |
| eumos/arch/rv64/instructions/I/LWU.yml | Sets `asm_format: offset_base` for canonical load syntax. |
| eumos/arch/rv64/instructions/I/LW.yml | Sets `asm_format: offset_base` for canonical load syntax. |
| eumos/arch/rv64/instructions/I/LHU.yml | Sets `asm_format: offset_base` for canonical load syntax. |
| eumos/arch/rv64/instructions/I/LH.yml | Sets `asm_format: offset_base` for canonical load syntax. |
| eumos/arch/rv64/instructions/I/LD.yml | Sets `asm_format: offset_base` for canonical load syntax. |
| eumos/arch/rv64/instructions/I/LBU.yml | Sets `asm_format: offset_base` for canonical load syntax. |
| eumos/arch/rv64/instructions/I/LB.yml | Sets `asm_format: offset_base` for canonical load syntax. |
| eumos/arch/rv64/instructions/I/JALR.yml | Sets `asm_format: offset_base` for canonical jalr syntax. |
| eumos/arch/rv64/formats/U.yml | Converts U format to `asm_formats`. |
| eumos/arch/rv64/formats/S.yml | Converts S format to `asm_formats` (offset-base form). |
| eumos/arch/rv64/formats/R.yml | Converts R format to `asm_formats`. |
| eumos/arch/rv64/formats/J.yml | Converts J format to `asm_formats`. |
| eumos/arch/rv64/formats/I.yml | Converts I format to `asm_formats` with `standard` + `offset_base`. |
| eumos/arch/rv64/formats/B.yml | Converts B format to `asm_formats`. |
| debug_regex.py | Adds a debugging script (currently lacks required license header). |
| README.md | Updates public docs for new `asm_formats` and decoder API (currently inaccurate in places). |
</details>






---

💡 <a href="/Alldred/eumos/new/main/.github/instructions?filename=*.instructions.md" class="Link--inTextBlock" target="_blank" rel="noopener noreferrer">Add Copilot custom instructions</a> for smarter, more guided reviews. <a href="https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot" class="Link--inTextBlock" target="_blank" rel="noopener noreferrer">Learn how to get started</a>.
--
