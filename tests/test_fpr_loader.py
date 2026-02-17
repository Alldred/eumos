# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Tests for fpr_loader.load_all_fprs."""

from eumos import constants, fpr_loader, models


def test_load_fprs_returns_dict():
    fprs = fpr_loader.load_all_fprs()
    assert isinstance(fprs, dict)
    assert len(fprs) == 32
    for i in range(32):
        assert i in fprs


def test_load_fprs_f0_ft0_read_write():
    fprs = fpr_loader.load_all_fprs()
    f0 = fprs[0]
    assert isinstance(f0, models.FPRDef)
    assert f0.index == 0
    assert f0.abi_name == "ft0"
    assert f0.reset_value == 0
    assert f0.access == "read-write"


def test_load_fprs_f10_fa0():
    fprs = fpr_loader.load_all_fprs()
    f10 = fprs[10]
    assert f10.abi_name == "fa0"
    assert f10.reset_value == 0
    assert f10.access == "read-write"


def test_load_fprs_abi_names():
    fprs = fpr_loader.load_all_fprs()
    for i, name in enumerate(constants.FPR_ABI_NAMES):
        assert fprs[i].abi_name == name


def test_load_fprs_source_file():
    fprs = fpr_loader.load_all_fprs()
    for i in range(32):
        assert fprs[i].source_file is not None
        assert "fprs" in fprs[i].source_file
