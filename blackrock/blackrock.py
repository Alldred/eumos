# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred. All Rights Reserved

"""Blackrock main class and arch_root normalization."""

from .csr_loader import load_all_csrs
from .format_loader import load_all_formats
from .gpr_loader import load_all_gprs
from .instruction_loader import load_all_instructions


class Blackrock:
    """
    Blackrock is the central class for loading and organizing RISC-V architecture data from YAML files.

    Attributes:
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

    def __init__(self):
        """Initialize Blackrock and load all architecture data from built-in package paths."""
        self.csrs = self._sorted_dict(load_all_csrs())
        self.gprs = self._sorted_dict(load_all_gprs())
        self.formats = self._sorted_dict(load_all_formats())
        self.instructions = self._sorted_dict(load_all_instructions())

    def _sorted_dict(self, d):
        if not isinstance(d, dict):
            return d
        return dict(sorted(d.items()))

    def reload(self):
        self.csrs = load_all_csrs()
        self.gprs = load_all_gprs()
        self.formats = load_all_formats()
        self.instructions = load_all_instructions()
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
