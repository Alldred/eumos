# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Shared RISC-V ABI and name constants (single source of truth for decoder and instance)."""

from typing import Dict, Tuple

# RISC-V FPR ABI names (f0..f31): ft0-ft7, fs0-fs1, fa0-fa7, fs2-fs11, ft8-ft11
FPR_ABI_NAMES: Tuple[str, ...] = (
    "ft0", "ft1", "ft2", "ft3", "ft4", "ft5", "ft6", "ft7",
    "fs0", "fs1",
    "fa0", "fa1", "fa2", "fa3", "fa4", "fa5", "fa6", "fa7",
    "fs2", "fs3", "fs4", "fs5", "fs6", "fs7", "fs8", "fs9", "fs10", "fs11",
    "ft8", "ft9", "ft10", "ft11",
)
FPR_NAME_TO_INDEX: Dict[str, int] = {}
for _i, _n in enumerate(FPR_ABI_NAMES):
    FPR_NAME_TO_INDEX[_n] = _i
for _i in range(32):
    FPR_NAME_TO_INDEX[f"f{_i}"] = _i
