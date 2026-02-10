# SPDX-License-Identifier: MIT
# Copyright (c) 2025-2026 Stuart Alldred. All Rights Reserved

import importlib.resources

from .csr_loader import load_all_csrs
from .format_loader import load_all_formats
from .gpr_loader import load_all_gprs
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
            # Use package-relative path for arch_root
            arch_root = importlib.resources.files("blackrock") / "arch" / "rv64"
        self.arch_root = arch_root
        self.csrs = self._sorted_dict(self._load_csrs())
        self.gprs = self._sorted_dict(self._load_gprs())
        self.formats = self._sorted_dict(self._load_formats())
        self.instructions = self._sorted_dict(self._load_instructions())

    def _sorted_dict(self, d):
        if not isinstance(d, dict):
            return d
        return dict(sorted(d.items()))

    def _load_csrs(self):
        csr_root = self.arch_root / "csrs"
        return load_all_csrs(csr_root)

    def _load_gprs(self):
        gpr_root = self.arch_root / "gprs"
        return load_all_gprs(gpr_root)

    def _load_formats(self):
        format_root = self.arch_root / "formats"
        return load_all_formats(format_root)

    def _load_instructions(self):
        instruction_root = self.arch_root / "instructions"
        return load_all_instructions(instruction_root)

    def reload(self):
        self.csrs = self._load_csrs()
        self.gprs = self._load_gprs()
        self.formats = self._load_formats()
        self.instructions = self._load_instructions()
        # Reset cached counts
        for attr in ("_gpr_count", "_csr_count", "_format_count", "_instruction_count"):
            if hasattr(self, attr):
                delattr(self, attr)

    @property
    def gpr_count(self):
        """Return the number of loaded GPRs (cached)."""
        if not hasattr(self, "_gpr_count"):
            self._gpr_count = len(self.gprs)
        return self._gpr_count

    @property
    def csr_count(self):
        """Return the number of loaded CSRs (cached)."""
        if not hasattr(self, "_csr_count"):
            self._csr_count = len(self.csrs)
        return self._csr_count

    @property
    def format_count(self):
        """Return the number of loaded instruction formats (cached)."""
        if not hasattr(self, "_format_count"):
            self._format_count = len(self.formats)
        return self._format_count

    @property
    def instruction_count(self):
        """Return the number of loaded instructions (cached)."""
        if not hasattr(self, "_instruction_count"):
            self._instruction_count = len(self.instructions)
        return self._instruction_count

    # Optionally add validation or other utility methods
