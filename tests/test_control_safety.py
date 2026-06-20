"""Pruebas de la capa de seguridad de infusion de insulina.

Estas pruebas son criticas: verifican que las salvaguardas vetan o limitan la
orden del controlador en las condiciones peligrosas. Un fallo aqui es un
fallo de seguridad.
"""

from diab_m1.control.safety import (
    SafetySupervisor,
    SafetyLimits,
    SafetyState,
    InsulinOnBoard,
)


def make_sup(**kw):
    lim = SafetyLimits(**kw)
    return SafetySupervisor(limits=lim, iob=InsulinOnBoard(), dt_min=5.0)


def test_low_glucose_forces_suspension():
    sup = make_sup()
    allowed, st = sup.evaluate(
        requested_uU_min=100000, glucose_mgdl=60, t_min=0.0
    )
    assert allowed == 0.0
    assert st is SafetyState.SUSPENDED_LOW


def test_predicted_low_forces_suspension():
    sup = make_sup(predicted_low_mgdl=80, prediction_horizon_min=30)
    # 100 mg/dL bajando 1 mg/dL/min -> 70 en 30 min -> por debajo de 80
    allowed, st = sup.evaluate(
        requested_uU_min=100000,
        glucose_mgdl=100,
        t_min=0.0,
        glucose_rate_mgdl_min=-1.0,
    )
    assert allowed == 0.0
    assert st is SafetyState.SUSPENDED_PREDICTED_LOW


def test_invalid_sensor_value_suspends():
    sup = make_sup()
    allowed, st = sup.evaluate(
        requested_uU_min=100000, glucose_mgdl=700, t_min=0.0
    )
    assert allowed == 0.0
    assert st is SafetyState.SUSPENDED_FAULT


def test_stale_sensor_suspends():
    sup = make_sup(max_sensor_age_min=15)
    allowed, st = sup.evaluate(
        requested_uU_min=100000,
        glucose_mgdl=150,
        t_min=0.0,
        sensor_age_min=20.0,
    )
    assert allowed == 0.0
    assert st is SafetyState.SUSPENDED_FAULT


def test_hard_dose_cap():
    sup = make_sup(
        max_infusion_uU_min=50000,
        max_delta_uU_min_per_min=1e12,  # desactiva rate limit
        max_iob_uU=1e15,                 # desactiva IOB cap
    )
    allowed, st = sup.evaluate(
        requested_uU_min=999999, glucose_mgdl=200, t_min=0.0
    )
    assert allowed == 50000
    assert st is SafetyState.DOSE_CAPPED


def test_rate_limiting():
    sup = make_sup(
        max_infusion_uU_min=1e12,
        max_delta_uU_min_per_min=1000.0,  # 1000 uU/min por minuto
        max_iob_uU=1e15,
    )
    # primer paso: desde 0, max incremento = 1000*5 = 5000
    allowed, st = sup.evaluate(
        requested_uU_min=100000, glucose_mgdl=200, t_min=0.0
    )
    assert allowed == 5000
    assert st is SafetyState.RATE_LIMITED


def test_iob_cap_blocks_when_full():
    sup = make_sup(
        max_iob_uU=1000.0,
        max_infusion_uU_min=1e12,
        max_delta_uU_min_per_min=1e12,
    )
    # precargar IOB por encima del tope
    sup.iob.add(2000.0, 0.0)
    allowed, st = sup.evaluate(
        requested_uU_min=100000, glucose_mgdl=200, t_min=0.0
    )
    assert allowed == 0.0
    assert st is SafetyState.IOB_CAPPED


def test_normal_passthrough_within_limits():
    sup = make_sup(
        max_infusion_uU_min=1e12,
        max_delta_uU_min_per_min=1e12,
        max_iob_uU=1e15,
    )
    allowed, st = sup.evaluate(
        requested_uU_min=1234, glucose_mgdl=160, t_min=0.0
    )
    assert allowed == 1234
    assert st is SafetyState.NORMAL


def test_resume_only_above_threshold():
    sup = make_sup(
        low_glucose_suspend_mgdl=70,
        resume_glucose_mgdl=90,
        predicted_low_mgdl=80,
    )
    # entra en suspension por baja
    sup.evaluate(requested_uU_min=10000, glucose_mgdl=65, t_min=0.0)
    # a 85 mg/dL todavia no reanuda (por debajo del umbral de reanudacion)
    allowed, st = sup.evaluate(
        requested_uU_min=10000, glucose_mgdl=85, t_min=5.0,
        glucose_rate_mgdl_min=0.0,
    )
    assert allowed == 0.0
    assert st is SafetyState.SUSPENDED_LOW
    # a 95 mg/dL estable, reanuda
    allowed, st = sup.evaluate(
        requested_uU_min=10000, glucose_mgdl=95, t_min=10.0,
        glucose_rate_mgdl_min=0.0,
    )
    assert allowed > 0.0


def test_iob_decays_over_time():
    iob = InsulinOnBoard(action_duration_min=300.0)
    iob.add(1.0e6, 0.0)
    early = iob.value(10.0)
    late = iob.value(280.0)
    assert late < early
