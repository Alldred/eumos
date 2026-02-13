# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Tests for gpr_loader.load_all_gprs."""

from eumos import gpr_loader, models


def test_load_gprs_returns_dict():
    gprs = gpr_loader.load_all_gprs()
    assert isinstance(gprs, dict)
    assert len(gprs) == 32
    for i in range(32):
        assert i in gprs


def test_load_gprs_x0_zero_read_only():
    gprs = gpr_loader.load_all_gprs()
    g0 = gprs[0]
    assert isinstance(g0, models.GPRDef)
    assert g0.index == 0
    assert g0.abi_name == "zero"
    assert g0.reset_value == 0
    assert g0.access == "read-only"


def test_load_gprs_x1_ra_read_write():
    gprs = gpr_loader.load_all_gprs()
    g1 = gprs[1]
    assert g1.abi_name == "ra"
    assert g1.reset_value == 0
    assert g1.access == "read-write"


def test_load_gprs_abi_names():
    gprs = gpr_loader.load_all_gprs()
    expected = (
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
    for i, name in enumerate(expected):
        assert gprs[i].abi_name == name
