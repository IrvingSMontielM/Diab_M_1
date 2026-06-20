"""Pruebas de las conversiones de unidades clinicas."""

import math

from diab_m1.units import (
    a1c_to_eag_mgdl,
    a1c_to_ifcc,
    eag_mgdl_to_a1c,
    ifcc_to_a1c,
    mgdl_to_mmoll,
    mmoll_to_mgdl,
)


def test_glucose_roundtrip():
    for mgdl in (70.0, 100.0, 126.0, 200.0, 350.0):
        assert math.isclose(mmoll_to_mgdl(mgdl_to_mmoll(mgdl)), mgdl, rel_tol=1e-9)


def test_diabetes_threshold_in_mmoll():
    # 126 mg/dL es el umbral diagnostico en ayunas.
    assert math.isclose(mgdl_to_mmoll(126.0), 6.9929, abs_tol=1e-3)


def test_ogtt_threshold_in_mmoll():
    # 200 mg/dL a las 2 h es el umbral diagnostico de OGTT.
    assert math.isclose(mgdl_to_mmoll(200.0), 11.1, abs_tol=0.05)


def test_a1c_ifcc_roundtrip():
    for a1c in (5.0, 5.7, 6.5, 7.0, 9.0):
        assert math.isclose(ifcc_to_a1c(a1c_to_ifcc(a1c)), a1c, rel_tol=1e-9)


def test_a1c_diabetes_threshold_in_ifcc():
    # NGSP 6.5% corresponde a ~48 mmol/mol (IFCC).
    assert math.isclose(a1c_to_ifcc(6.5), 48.0, abs_tol=0.6)


def test_eag_from_a1c_adag():
    # Formula ADAG: eAG[mg/dL] = 28.7 * A1c - 46.7.
    assert math.isclose(a1c_to_eag_mgdl(6.0), 125.5, abs_tol=0.5)
    assert math.isclose(a1c_to_eag_mgdl(7.0), 154.2, abs_tol=0.5)


def test_eag_a1c_roundtrip():
    for a1c in (5.5, 6.5, 8.0):
        assert math.isclose(eag_mgdl_to_a1c(a1c_to_eag_mgdl(a1c)), a1c, rel_tol=1e-9)
