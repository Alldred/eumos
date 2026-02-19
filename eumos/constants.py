# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Shared RISC-V ABI and name constants (single source of truth for decoder and instance)."""

from typing import Dict, Tuple

# RISC-V rounding modes (frm field and instruction rm)
RNE = 0  # Round to Nearest, ties to Even
RTZ = 1  # Round towards Zero
RDN = 2  # Round Down (towards -inf)
RUP = 3  # Round Up (towards +inf)
RMM = 4  # Round to Nearest, ties to Max Magnitude
R_DYN = 7  # Dynamic: use frm from fcsr

# RISC-V GPR ABI names (x0..x31). s0/fp is canonical as s0.
GPR_ABI_NAMES: Tuple[str, ...] = (
    "zero",
    "ra",
    "sp",
    "gp",
    "tp",
    "t0",
    "t1",
    "t2",
    "s0",
    "s1",
    "a0",
    "a1",
    "a2",
    "a3",
    "a4",
    "a5",
    "a6",
    "a7",
    "s2",
    "s3",
    "s4",
    "s5",
    "s6",
    "s7",
    "s8",
    "s9",
    "s10",
    "s11",
    "t3",
    "t4",
    "t5",
    "t6",
)
GPR_NAME_TO_INDEX: Dict[str, int] = {}
for _i, _n in enumerate(GPR_ABI_NAMES):
    GPR_NAME_TO_INDEX[_n] = _i
for _i in range(32):
    GPR_NAME_TO_INDEX[f"x{_i}"] = _i
GPR_NAME_TO_INDEX["fp"] = 8  # s0/fp

# RISC-V FPR ABI names (f0..f31): ft0-ft7, fs0-fs1, fa0-fa7, fs2-fs11, ft8-ft11
FPR_ABI_NAMES: Tuple[str, ...] = (
    "ft0",
    "ft1",
    "ft2",
    "ft3",
    "ft4",
    "ft5",
    "ft6",
    "ft7",
    "fs0",
    "fs1",
    "fa0",
    "fa1",
    "fa2",
    "fa3",
    "fa4",
    "fa5",
    "fa6",
    "fa7",
    "fs2",
    "fs3",
    "fs4",
    "fs5",
    "fs6",
    "fs7",
    "fs8",
    "fs9",
    "fs10",
    "fs11",
    "ft8",
    "ft9",
    "ft10",
    "ft11",
)
FPR_NAME_TO_INDEX: Dict[str, int] = {}
for _i, _n in enumerate(FPR_ABI_NAMES):
    FPR_NAME_TO_INDEX[_n] = _i
for _i in range(32):
    FPR_NAME_TO_INDEX[f"f{_i}"] = _i
