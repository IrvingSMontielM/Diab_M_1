"""Modelo de regulacion glucosa-insulina de Stolwijk-Hardy (Khoo, 2018).

Reimplementacion en Python (SciPy) del modelo descrito en la propuesta, que
en el trabajo original se construyo en Simulink. Se trata de dos ecuaciones
diferenciales no lineales acopladas de primer orden.

Variables de estado
-------------------
- x : concentracion plasmatica de glucosa [mg/mL]   (81 mg/dL = 0.81 mg/mL)
- y : concentracion plasmatica de insulina [mU/mL]

Ecuaciones (forma de balance de masa con volumenes de distribucion):

    dx/dt = ( Q_L + u(t) - lambda*x - nu*x*y - mu*max(x - theta, 0) ) / Vg
    dy/dt = ( beta*max(x - phi, 0) - alpha*y ) / Vi

donde u(t) es la tasa de glucosa exogena (comidas) en mg/h.

Notas de fidelidad
------------------
La estructura de las ecuaciones y los parametros de la Tabla I provienen de
Khoo, "Physiological Control Systems" (2018), basado a su vez en Stolwijk &
Hardy (1974). Los volumenes Vg y Vi no aparecen en la tabla original; aqui se
introducen explicitamente para fijar la escala temporal en valores
fisiologicos. El punto de equilibrio basal (x0 ~ 0.81 mg/mL, y0 ~ 0.056
mU/mL) es INDEPENDIENTE de Vg y Vi y reproduce el reportado en la propuesta.
El termino renal mu*max(x - theta, 0) solo actua en hiperglucemia severa
(x > theta = 2.5 mg/mL = 250 mg/dL). Para coincidencia cuantitativa exacta
con un build de Simulink especifico, verifique el escalado interno de ese
modelo.

Este modelo es ilustrativo y de investigacion. No representa a ningun
paciente real ni debe usarse para decisiones clinicas.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Optional

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class StolwijkHardyParams:
    """Parametros del modelo (Tabla I, Khoo 2018) mas volumenes de escala."""

    theta: float = 2.5       # umbral renal de glucosa [mg/mL]
    mu: float = 7200.0       # utilizacion/perdida renal sobre umbral [mL/h]
    lam: float = 2470.0      # aclaramiento hepatico/insulino-independiente [mL/h]
    nu: float = 139000.0     # captacion tisular dependiente de insulina [1/(mU*h)]
    phi: float = 0.51        # umbral de secrecion de insulina [mg/mL]
    beta: float = 1430.0     # sensibilidad de secrecion pancreatica
    alpha: float = 7600.0    # degradacion de insulina [mL/h]
    q_l: float = 8400.0      # produccion hepatica basal de glucosa [mg/h]
    vg: float = 10000.0      # volumen de distribucion de glucosa [mL]
    vi: float = 760.0        # volumen de distribucion de insulina [mL]


def healthy_params() -> StolwijkHardyParams:
    """Sujeto sano: parametros nominales."""
    return StolwijkHardyParams()


def dm1_params(secretion_fraction: float = 0.2) -> StolwijkHardyParams:
    """Diabetes tipo 1: secrecion pancreatica reducida (beta al 20%)."""
    base = StolwijkHardyParams()
    return replace(base, beta=base.beta * secretion_fraction)


def dm2_params(sensitivity_fraction: float = 0.2) -> StolwijkHardyParams:
    """Diabetes tipo 2: resistencia periferica (nu al 20%)."""
    base = StolwijkHardyParams()
    return replace(base, nu=base.nu * sensitivity_fraction)


def _rhs(
    t: float,
    state: np.ndarray,
    p: StolwijkHardyParams,
    u_glucose: Callable[[float], float],
) -> list[float]:
    x, y = state
    renal = p.mu * max(x - p.theta, 0.0)
    secretion = p.beta * max(x - p.phi, 0.0)
    dxdt = (p.q_l + u_glucose(t) - p.lam * x - p.nu * x * y - renal) / p.vg
    dydt = (secretion - p.alpha * y) / p.vi
    return [dxdt, dydt]


def equilibrium(p: StolwijkHardyParams) -> tuple[float, float]:
    """Punto de equilibrio (x*, y*) en ayuno (u=0), resuelto numericamente.

    Sustituyendo y* = beta*(x*-phi)/alpha en dx/dt=0 (asumiendo x* < theta,
    sin perdida renal) se obtiene una cuadratica en x*.
    """
    a = p.nu * p.beta / p.alpha
    b = p.lam - a * p.phi
    c = -p.q_l
    # a*x^2 + b*x + c = 0
    disc = b * b - 4 * a * c
    x_star = (-b + np.sqrt(disc)) / (2 * a)
    y_star = p.beta * max(x_star - p.phi, 0.0) / p.alpha
    return float(x_star), float(y_star)


def simulate(
    params: StolwijkHardyParams,
    u_glucose: Callable[[float], float],
    hours: float = 24.0,
    x0: Optional[float] = None,
    y0: Optional[float] = None,
    max_step_h: float = 0.05,
) -> dict:
    """Integra el modelo durante `hours` horas.

    Parameters
    ----------
    params : StolwijkHardyParams
    u_glucose : callable t[h] -> tasa de glucosa exogena [mg/h]
    hours : horizonte de simulacion en horas
    x0, y0 : condiciones iniciales; por defecto el equilibrio de `params`
    max_step_h : paso maximo del integrador

    Returns
    -------
    dict con 't_h', 'glucose_mgdl', 'insulin_muml', 'x_mgml', 'y_muml'.
    """
    if x0 is None or y0 is None:
        xe, ye = equilibrium(params)
        x0 = xe if x0 is None else x0
        y0 = ye if y0 is None else y0

    sol = solve_ivp(
        _rhs,
        (0.0, hours),
        [x0, y0],
        args=(params, u_glucose),
        max_step=max_step_h,
        rtol=1e-6,
        atol=1e-9,
        dense_output=False,
    )
    if not sol.success:
        raise RuntimeError(f"Integracion fallida: {sol.message}")

    x = sol.y[0]
    y = sol.y[1]
    return {
        "t_h": sol.t,
        "x_mgml": x,
        "y_muml": y,
        "glucose_mgdl": x * 100.0,  # mg/mL -> mg/dL
        "insulin_muml": y,
    }
