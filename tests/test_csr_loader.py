# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred

# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Stuart Alldred.

"""Tests for csr_loader.load_all_csrs."""

from eumos import csr_loader, models


def test_load_csr_mstatus():
    csrs = csr_loader.load_all_csrs()
    csr = csrs["mstatus"]
    assert isinstance(csr, models.CSRDef)
    assert csr.name == "mstatus"
    assert csr.address == 0x300
    assert "status" in csr.description.lower()
    assert csr.privilege == "machine"
    assert csr.access == "read-write"
    assert csr.width == 64
    assert csr.extension == "Zicsr"
    assert csr.reset_value == 0


def test_load_csr_mstatus_has_fields():
    csrs = csr_loader.load_all_csrs()
    csr = csrs["mstatus"]
    assert csr.fields is not None
    assert "MIE" in csr.fields
    assert "MPIE" in csr.fields
    assert "MPP" in csr.fields
    mie = csr.fields["MIE"]
    assert isinstance(mie, models.CSRFieldDef)
    assert mie.name == "MIE"
    assert mie.bits == 3
    assert mie.access is None  # uses CSR default
    mpp = csr.fields["MPP"]
    assert mpp.bits == (12, 11)
    assert "reserved" in csr.fields
    assert csr.fields["reserved"].bits == (2, 0)
    assert "reserved1" in csr.fields
    assert "reserved3" in csr.fields
    assert csr.fields["reserved3"].bits == (63, 13)


def test_load_csr_mepc_has_reset_value_and_full_width_field():
    csrs = csr_loader.load_all_csrs()
    mepc = csrs["mepc"]
    assert mepc.reset_value == 0
    assert mepc.fields is not None
    assert "value" in mepc.fields
    assert mepc.fields["value"].bits == (63, 0)


def test_load_all_csrs_returns_dict():
    csrs = csr_loader.load_all_csrs()
    assert isinstance(csrs, dict)
    assert "mstatus" in csrs
    assert "mepc" in csrs
    assert "mcause" in csrs
    assert "mtvec" in csrs
    assert csrs["mstatus"].address == 0x300
    assert csrs["mepc"].address == 0x341
    assert csrs["mcause"].address == 0x342
    assert len(csrs) == 16
