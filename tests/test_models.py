"""Pruebas de los modelos fisiologicos (Stolwijk-Hardy y Bergman)."""

import numpy as np

from diab_m1.models.bergman import (
    BergmanParams,
    basal_insulin_infusion,
    simulate_open_loop,
)
from diab_m1.models.stolwijk_hardy import (
    dm1_params,
    dm2_params,
    equilibrium,
    healthy_params,
    simulate,
)


# ----------------------------------------------------------------------------
# Stolwijk-Hardy
# ----------------------------------------------------------------------------
def test_healthy_basal_matches_pdf():
    # El PDF reporta x0 ~ 0.81 mg/mL (=> 81 mg/dL) e y0 ~ 0.056 mU/mL.
    x_star, y_star = equilibrium(healthy_params())
    assert 0.78 <= x_star <= 0.84
    assert 0.045 <= y_star <= 0.065


def test_equilibrium_is_a_fixed_point():
    # Con entrada nula el sistema debe permanecer en el equilibrio.
    p = healthy_params()
    x_star, y_star = equilibrium(p)
    out = simulate(p, u_glucose=lambda t: 0.0, hours=12.0)
    assert np.isclose(out["x_mgml"][-1], x_star, atol=1e-3)
    assert np.isclose(out["y_muml"][-1], y_star, atol=1e-3)


def test_dm1_has_low_insulin_relative_to_healthy():
    _, y_healthy = equilibrium(healthy_params())
    _, y_dm1 = equilibrium(dm1_params())
    assert y_dm1 < y_healthy


def test_dm2_has_high_insulin_relative_to_healthy():
    _, y_healthy = equilibrium(healthy_params())
    _, y_dm2 = equilibrium(dm2_params())
    assert y_dm2 > y_healthy


def test_diabetic_basal_glucose_is_elevated():
    x_healthy, _ = equilibrium(healthy_params())
    x_dm1, _ = equilibrium(dm1_params())
    x_dm2, _ = equilibrium(dm2_params())
    assert x_dm1 > x_healthy
    assert x_dm2 > x_healthy


# ----------------------------------------------------------------------------
# Bergman
# ----------------------------------------------------------------------------
def test_bergman_basal_reaches_stable_euglycemia():
    # Con la tasa basal nominal y sin comidas, la glucosa converge a un estado
    # estacionario euglucemico estable (no necesariamente igual a gb).
    p = BergmanParams()
    u_basal = basal_insulin_infusion(p)
    out = simulate_open_loop(
        p, ra=lambda t: 0.0, u_ins=lambda t: u_basal, minutes=8 * 60.0
    )
    g = out["glucose_mgdl"]
    assert 70.0 <= g[-1] <= 95.0  # euglucemia
    assert np.ptp(g[-12:]) < 0.5  # plano en la ultima hora (dt=1 min)


def test_bergman_meal_raises_glucose_without_extra_insulin():
    # Una comida (Ra positivo) sin bolo debe elevar la glucosa por encima de gb.
    p = BergmanParams()
    u_basal = basal_insulin_infusion(p)

    def ra(t):
        # pico de aparicion de glucosa centrado a los 30 min
        return 4.0 * np.exp(-((t - 30.0) ** 2) / (2 * 20.0**2))

    out = simulate_open_loop(p, ra=ra, u_ins=lambda t: u_basal, minutes=6 * 60.0)
    assert out["glucose_mgdl"].max() > p.gb + 20.0


def test_insulin_sensitivity_positive():
    assert BergmanParams().insulin_sensitivity > 0.0
