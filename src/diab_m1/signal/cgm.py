"""Procesamiento de senal de glucosa (CGM/SMBG) y metricas de exactitud.

Incluye:
- Filtrado causal de la senal de un monitor continuo (CGM) ruidoso y
  estimacion de la pendiente (rate of change).
- Verificacion de exactitud analitica segun ISO 15197:2013 y segun la guia
  de la FDA de 2016 (mas estricta) para sistemas de automonitoreo.
- Clasificacion por zonas de la rejilla de error de Clarke (Clarke Error
  Grid), una herramienta estandar para evaluar la relevancia clinica del
  error de un glucometro.

Referencias de los criterios de exactitud:
  ISO 15197:2013: >= 95% de los resultados dentro de +/-15 mg/dL (para
  glucosa < 100 mg/dL) o +/-15% (para glucosa >= 100 mg/dL) frente al
  metodo de referencia; ademas 99% en zonas A y B de una rejilla de error
  de consenso.
  FDA (Self-Monitoring Blood Glucose Test Systems, 2016): 95% dentro de
  +/-15% y 99% dentro de +/-20% en todo el rango de medicion.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ----------------------------------------------------------------------------
# Filtrado de CGM
# ----------------------------------------------------------------------------
def ewma_filter(signal: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    """Filtro exponencial causal (EWMA). alpha en (0, 1]; menor = mas suave."""
    signal = np.asarray(signal, dtype=float)
    out = np.empty_like(signal)
    acc = signal[0]
    for i, s in enumerate(signal):
        acc += alpha * (s - acc)
        out[i] = acc
    return out


def estimate_rate(
    signal: np.ndarray, dt_min: float, window: int = 5
) -> np.ndarray:
    """Pendiente [mg/dL/min] por regresion lineal causal en ventana movil.

    Para cada punto usa los ultimos `window` valores (o los disponibles).
    """
    signal = np.asarray(signal, dtype=float)
    n = len(signal)
    rate = np.zeros(n)
    for i in range(n):
        lo = max(0, i - window + 1)
        ys = signal[lo : i + 1]
        m = len(ys)
        if m < 2:
            rate[i] = 0.0
            continue
        xs = np.arange(m) * dt_min
        # pendiente de minimos cuadrados
        xbar = xs.mean()
        ybar = ys.mean()
        denom = ((xs - xbar) ** 2).sum()
        rate[i] = ((xs - xbar) * (ys - ybar)).sum() / denom if denom > 0 else 0.0
    return rate


# ----------------------------------------------------------------------------
# Exactitud analitica
# ----------------------------------------------------------------------------
@dataclass
class AccuracyResult:
    n: int
    pct_within: float
    passes: bool
    standard: str
    detail: str


def iso15197_accuracy(
    measured_mgdl: np.ndarray, reference_mgdl: np.ndarray
) -> AccuracyResult:
    """Evalua el criterio de exactitud de sistema de ISO 15197:2013.

    >= 95% de los pares dentro de +/-15 mg/dL (ref < 100) o +/-15% (ref>=100).
    """
    measured = np.asarray(measured_mgdl, dtype=float)
    reference = np.asarray(reference_mgdl, dtype=float)
    if measured.shape != reference.shape:
        raise ValueError("measured y reference deben tener la misma forma")

    diff = np.abs(measured - reference)
    tol = np.where(reference < 100.0, 15.0, 0.15 * reference)
    within = diff <= tol
    pct = 100.0 * within.mean()
    return AccuracyResult(
        n=len(measured),
        pct_within=pct,
        passes=pct >= 95.0,
        standard="ISO 15197:2013",
        detail=(
            f"{pct:.1f}% dentro de +/-15 mg/dL (<100) o +/-15% (>=100); "
            "criterio: >=95%"
        ),
    )


def fda_2016_accuracy(
    measured_mgdl: np.ndarray, reference_mgdl: np.ndarray
) -> AccuracyResult:
    """Evalua la guia FDA 2016: 95% dentro de +/-15% y 99% dentro de +/-20%."""
    measured = np.asarray(measured_mgdl, dtype=float)
    reference = np.asarray(reference_mgdl, dtype=float)
    rel = np.abs(measured - reference) / reference * 100.0
    pct15 = 100.0 * (rel <= 15.0).mean()
    pct20 = 100.0 * (rel <= 20.0).mean()
    passes = pct15 >= 95.0 and pct20 >= 99.0
    return AccuracyResult(
        n=len(measured),
        pct_within=pct15,
        passes=passes,
        standard="FDA 2016 (SMBG)",
        detail=(
            f"{pct15:.1f}% dentro de +/-15% (req >=95%); "
            f"{pct20:.1f}% dentro de +/-20% (req >=99%)"
        ),
    )


# ----------------------------------------------------------------------------
# Rejilla de error de Clarke
# ----------------------------------------------------------------------------
def clarke_error_grid_zone(reference_mgdl: float, measured_mgdl: float) -> str:
    """Devuelve la zona ('A'..'E') de la rejilla de error de Clarke.

    Implementacion de las regiones de Clarke et al. (Diabetes Care, 1987).
    A: clinicamente exacta; B: error benigno; C/D/E: error con potencial
    relevancia clinica creciente.
    """
    ref = float(reference_mgdl)
    meas = float(measured_mgdl)

    # Zona A: dentro de +/-20% del valor de referencia, o ambos < 70 mg/dL.
    if (ref <= 70 and meas <= 70) or (ref > 0 and abs(meas - ref) <= 0.2 * ref):
        return "A"

    # Zona E: error contradictorio (trata hipo como hiper o viceversa).
    if (ref >= 180 and meas <= 70) or (ref <= 70 and meas >= 180):
        return "E"

    # Zona C: sobrecorreccion.
    if (
        (ref >= 70 and ref <= 290 and meas >= ref + 110)
        or (ref >= 130 and ref <= 180 and meas <= (7.0 / 5.0) * ref - 182)
    ):
        return "C"

    # Zona D: no detecta una desviacion peligrosa.
    if (ref < 70 and meas >= 70 and meas <= 180) or (
        ref > 240 and 70 <= meas <= 180
    ):
        return "D"

    # Resto: zona B (error benigno que no lleva a tratamiento inapropiado).
    return "B"


def clarke_zone_distribution(
    reference_mgdl: np.ndarray, measured_mgdl: np.ndarray
) -> dict[str, float]:
    """Porcentaje de pares en cada zona de Clarke."""
    reference = np.asarray(reference_mgdl, dtype=float)
    measured = np.asarray(measured_mgdl, dtype=float)
    zones = [clarke_error_grid_zone(r, m) for r, m in zip(reference, measured)]
    n = len(zones)
    return {
        z: 100.0 * zones.count(z) / n for z in ["A", "B", "C", "D", "E"]
    }
