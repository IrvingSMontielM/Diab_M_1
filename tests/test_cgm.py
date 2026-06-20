"""Pruebas del procesamiento de senal CGM y metricas de exactitud."""

import numpy as np

from diab_m1.signal.cgm import (
    clarke_error_grid_zone,
    clarke_zone_distribution,
    estimate_rate,
    ewma_filter,
    fda_2016_accuracy,
    iso15197_accuracy,
)


def test_ewma_smooths_noise():
    rng = np.random.default_rng(0)
    clean = np.full(200, 120.0)
    noisy = clean + rng.normal(0, 10, size=clean.shape)
    filt = ewma_filter(noisy, alpha=0.2)
    assert filt.std() < noisy.std()


def test_estimate_rate_on_linear_ramp():
    dt = 5.0
    # rampa de 2 mg/dL por minuto
    t = np.arange(0, 60, dt)
    signal = 100.0 + 2.0 * t
    rate = estimate_rate(signal, dt_min=dt, window=5)
    # despues de llenar la ventana, la pendiente estimada debe ser ~2
    assert np.allclose(rate[-3:], 2.0, atol=1e-6)


def test_iso15197_perfect_match_passes():
    ref = np.array([60, 90, 120, 180, 250, 350], dtype=float)
    res = iso15197_accuracy(measured_mgdl=ref.copy(), reference_mgdl=ref)
    assert res.pct_within == 100.0
    assert res.passes


def test_iso15197_large_bias_fails():
    ref = np.full(100, 200.0)
    measured = ref * 1.30  # 30% de sesgo, fuera de +/-15%
    res = iso15197_accuracy(measured_mgdl=measured, reference_mgdl=ref)
    assert not res.passes


def test_fda_2016_is_stricter_than_iso_on_borderline():
    rng = np.random.default_rng(1)
    ref = rng.uniform(70, 300, size=500)
    # ruido relativo del 12%: pasa ISO pero suele fallar el 99% dentro de 20%
    measured = ref * (1 + rng.normal(0, 0.12, size=ref.shape))
    iso = iso15197_accuracy(measured_mgdl=measured, reference_mgdl=ref)
    fda = fda_2016_accuracy(measured_mgdl=measured, reference_mgdl=ref)
    assert iso.pct_within >= fda.pct_within - 1e-9


def test_clarke_zone_a_for_exact_match():
    for g in (60.0, 110.0, 250.0):
        assert clarke_error_grid_zone(reference_mgdl=g, measured_mgdl=g) == "A"


def test_clarke_distribution_sums_to_100():
    ref = np.array([80, 120, 160, 200, 240], dtype=float)
    measured = ref + np.array([5, -10, 8, -15, 12], dtype=float)
    dist = clarke_zone_distribution(measured_mgdl=measured, reference_mgdl=ref)
    assert abs(sum(dist.values()) - 100.0) < 1e-6
