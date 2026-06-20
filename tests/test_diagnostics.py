"""Pruebas de la clasificacion diagnostica.

Verifican los puntos de corte ADA/OMS, la logica de confirmacion y el manejo
de unidades. La correctitud clinica de estos limites es critica.
"""

import pytest

from diab_m1.diagnostics import classify, Criteria, GlycemicStatus


def test_fpg_normal():
    r = classify(fpg_mg_dl=90)
    assert r.overall is GlycemicStatus.NORMAL


def test_fpg_prediabetes_ada_vs_who():
    # 105 mg/dL es prediabetes para ADA (>=100) pero normal para OMS (<110).
    assert classify(fpg_mg_dl=105, criteria=Criteria.ADA).overall is GlycemicStatus.PREDIABETES
    assert classify(fpg_mg_dl=105, criteria=Criteria.WHO).overall is GlycemicStatus.NORMAL


def test_fpg_diabetes_single_requires_confirmation():
    r = classify(fpg_mg_dl=140)
    assert r.overall is GlycemicStatus.DIABETES
    assert r.requires_confirmation is True


def test_two_tests_diabetes_no_confirmation():
    # FPG y A1c ambos diabeticos -> criterio cumplido sin confirmacion extra.
    r = classify(fpg_mg_dl=140, a1c_percent=7.2)
    assert r.overall is GlycemicStatus.DIABETES
    assert r.requires_confirmation is False


def test_a1c_boundaries():
    assert classify(a1c_percent=5.6).overall is GlycemicStatus.NORMAL
    assert classify(a1c_percent=6.0).overall is GlycemicStatus.PREDIABETES
    assert classify(a1c_percent=6.5).overall is GlycemicStatus.DIABETES


def test_ogtt_boundaries():
    assert classify(ogtt_2h_mg_dl=139).overall is GlycemicStatus.NORMAL
    assert classify(ogtt_2h_mg_dl=160).overall is GlycemicStatus.PREDIABETES
    assert classify(ogtt_2h_mg_dl=200).overall is GlycemicStatus.DIABETES


def test_random_with_symptoms_is_unequivocal():
    r = classify(random_glucose_mg_dl=260, classic_symptoms=True)
    assert r.overall is GlycemicStatus.DIABETES
    assert r.requires_confirmation is False


def test_random_without_symptoms_needs_standard_test():
    r = classify(random_glucose_mg_dl=260, classic_symptoms=False)
    # marcado como diabetico pero requiere confirmacion con prueba estandar
    assert r.requires_confirmation is True


def test_units_mmol_l():
    # 7.0 mmol/L = 126 mg/dL -> umbral diabetico de FPG
    r = classify(fpg_mg_dl=7.0, units="mmol/L")
    assert r.overall is GlycemicStatus.DIABETES


def test_no_input_indeterminate():
    r = classify()
    assert r.overall is GlycemicStatus.INDETERMINATE


def test_summary_renders():
    r = classify(fpg_mg_dl=130, a1c_percent=6.8)
    s = r.summary()
    assert "diabetes" in s.lower()
    assert "no es diagnostico" in s.lower()
