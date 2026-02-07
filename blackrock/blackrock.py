# SPDX-License-Identifier: MIT
# Copyright (c) 2025-2026 Stuart Alldred. All Rights Reserved

import os

from .csr_loader import load_all_csrs
from .format_loader import load_all_formats
from .gpr_loader import load_gpr
from .instruction_loader import load_all_instructions


class Blackrock:
    """
    Blackrock is the central class for loading and organizing RISC-V architecture data from YAML files.

    Attributes:
        arch_root (str): Root directory for architecture data.
        csrs (dict): Loaded Control and Status Registers.
        gprs (dict): Loaded General Purpose Registers.
        formats (dict): Loaded instruction formats.
        instructions (dict): Loaded instructions.

    Example:
        br = Blackrock()
        print(br.csrs)
        print(br.gprs)
        print(br.formats)
        print(br.instructions)
    """

    def __init__(self, arch_root: str = None):
        if arch_root is None:
            env_root = os.environ["BLACKROCK_ROOT"]
            arch_root = os.path.join(env_root, "arch", "rv64")
        self.arch_root = arch_root
        self.csrs = self._load_csrs()
        self.gprs = self._load_gprs()
        self.formats = self._load_formats()
        self.instructions = self._load_instructions()

    def _load_csrs(self):
        csr_root = os.path.join(self.arch_root, "csrs")
        return load_all_csrs(csr_root)

    def _load_gprs(self):
        gpr_path = os.path.join(self.arch_root, "gprs.yml")
        return load_gpr(gpr_path)

    def _load_formats(self):
        format_root = os.path.join(self.arch_root, "formats")
        return load_all_formats(format_root)

    def _load_instructions(self):
        instruction_root = os.path.join(self.arch_root, "instructions")
        return load_all_instructions(instruction_root)

    def reload(self):
        self.csrs = self._load_csrs()
        self.gprs = self._load_gprs()
        self.formats = self._load_formats()
        self.instructions = self._load_instructions()

    # Optionally add validation or other utility methods
