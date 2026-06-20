"""Modelo minimo de Bergman extendido como paciente virtual de DT1.

El modelo minimo de Bergman (Bergman et al., 1981) es un estandar de la
investigacion en control de glucosa por su balance entre simplicidad y
realismo dinamico. Aqui se usa como "planta" para probar el lazo cerrado del
controlador PID sobre un paciente virtual con diabetes tipo 1 (sin secrecion
endogena de insulina).

Variables de estado
-------------------
- G : glucosa plasmatica [mg/dL]
- X : accion insulinica remota [1/min]
- I : insulina plasmatica [uU/mL]

Ecuaciones:

    dG/dt = -(p1 + X) * G + p1 * Gb + Ra(t) / Vg
    dX/dt = -p2 * X + p3 * (I - Ib)
    dI/dt = -n * (I - Ib) + u_ins(t) / Vi

donde Ra(t) es la aparicion de glucosa por comidas [mg/dL/min equivalente,
ya dividida por Vg en el modulo de comidas] y u_ins(t) es la infusion
exogena de insulina [uU/min]. La sensibilidad a la insulina es SI = p3/p2.

Paciente virtual exclusivamente para simulacion e investigacion. No
representa a ninguna persona ni autoriza ninguna terapia.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class BergmanParams:
    p1: float = 0.028      # efectividad de la glucosa [1/min]
    p2: float = 0.025      # tasa de decaimiento de la accion remota [1/min]
    p3: float = 1.0e-5     # [mL/(uU*min^2)]
    n: float = 0.09        # aclaramiento de insulina [1/min]
    gb: float = 90.0       # glucosa basal [mg/dL]
    ib: float = 7.0        # insulina basal [uU/mL]
    vg_dl: float = 117.0   # volumen de distribucion de glucosa [dL]
    vi_ml: float = 12000.0 # volumen de distribucion de insulina [mL]

    @property
    def insulin_sensitivity(self) -> float:
        """SI = p3 / p2 [mL/(uU*min) por unidad]."""
        return self.p3 / self.p2


def basal_insulin_infusion(p: BergmanParams) -> float:
    """Tasa basal nominal de referencia [uU/min] para el lazo abierto.

    Devuelve ``n * ib * vi``. Bajo la convencion del modelo (la insulina relaja
    hacia ``ib`` por si sola), esta tasa no fija la glucosa exactamente en
    ``gb``: el sistema alcanza un estado estacionario euglucemico estable algo
    por debajo de ``gb``. Sirve como infusion basal de comparacion frente al
    lazo cerrado, no como garantia de fijacion de glucosa.
    """
    return p.n * p.ib * p.vi_ml


def _rhs(
    t: float,
    state: np.ndarray,
    p: BergmanParams,
    ra: Callable[[float], float],
    u_ins: Callable[[float], float],
) -> list[float]:
    G, X, I = state
    dGdt = -(p1_plus_X := (p.p1 + X)) * G + p.p1 * p.gb + ra(t)
    dXdt = -p.p2 * X + p.p3 * (I - p.ib)
    dIdt = -p.n * (I - p.ib) + u_ins(t) / p.vi_ml
    return [dGdt, dXdt, dIdt]


def simulate_open_loop(
    params: BergmanParams,
    ra: Callable[[float], float],
    u_ins: Callable[[float], float],
    minutes: float = 24 * 60.0,
    g0: Optional[float] = None,
    max_step_min: float = 1.0,
) -> dict:
    """Integra el modelo en lazo abierto con infusion u_ins(t) dada."""
    p = params
    g0 = p.gb if g0 is None else g0
    sol = solve_ivp(
        _rhs,
        (0.0, minutes),
        [g0, 0.0, p.ib],
        args=(p, ra, u_ins),
        max_step=max_step_min,
        rtol=1e-6,
        atol=1e-9,
    )
    if not sol.success:
        raise RuntimeError(f"Integracion fallida: {sol.message}")
    return {
        "t_min": sol.t,
        "glucose_mgdl": sol.y[0],
        "x_action": sol.y[1],
        "insulin_uuml": sol.y[2],
    }
