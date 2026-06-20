"""Capa de seguridad supervisora para administracion de insulina.

Esta capa es el componente de ingenieria biomedica mas critico del proyecto.
Replica las salvaguardas que llevan los sistemas reales de administracion
automatica de insulina (AID) aprobados (p. ej. la suspension predictiva por
glucosa baja de Control-IQ y Omnipod 5, y el "control de seguridad
redundante" de los sistemas tipo pancreas artificial). Su funcion es acotar
y, si es necesario, vetar la orden del controlador antes de que llegue a la
bomba.

Salvaguardas implementadas
--------------------------
1. Limite duro de tasa de infusion (basal/bolo maximo).
2. Limite de velocidad de cambio de la orden (rate limiting).
3. Insulina activa (IOB) con curva de accion y tope de IOB.
4. Suspension por glucosa baja (LGS) y suspension predictiva (PLGS): si la
   glucosa esta por debajo, o se predice por debajo de un umbral dentro de
   un horizonte, la infusion se fuerza a cero.
5. Suspension por dato invalido o "viejo" del sensor (deteccion de falla).

NINGUNA de estas salvaguardas convierte el sistema en un producto clinico.
El veto de seguridad reduce riesgo en simulacion y documenta el diseno
defensivo exigido por ISO 14971 / IEC 62304; no sustituye verificacion,
validacion ni autorizacion regulatoria. Ver DISCLAIMER.md.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SafetyState(str, Enum):
    NORMAL = "normal"
    RATE_LIMITED = "limitada_por_velocidad"
    DOSE_CAPPED = "limitada_por_tope"
    IOB_CAPPED = "limitada_por_iob"
    SUSPENDED_LOW = "suspendida_glucosa_baja"
    SUSPENDED_PREDICTED_LOW = "suspendida_prediccion_baja"
    SUSPENDED_FAULT = "suspendida_falla_sensor"


@dataclass
class SafetyLimits:
    max_infusion_uU_min: float = 250000.0  # tope duro de infusion [uU/min]
    max_delta_uU_min_per_min: float = 50000.0  # cambio maximo por minuto
    max_iob_uU: float = 8.0e6  # tope de insulina activa [uU]
    low_glucose_suspend_mgdl: float = 70.0  # umbral de suspension
    predicted_low_mgdl: float = 80.0  # umbral predictivo
    prediction_horizon_min: float = 30.0  # horizonte de prediccion
    resume_glucose_mgdl: float = 90.0  # reanudar por encima de este valor
    max_sensor_age_min: float = 15.0  # antiguedad maxima del dato valido
    glucose_valid_range_mgdl: tuple[float, float] = (20.0, 600.0)


@dataclass
class InsulinOnBoard:
    """Estimador simple de insulina activa con decaimiento bi-exponencial.

    Aproxima la curva de accion de un analogo rapido (accion ~5-6 h) como un
    decaimiento exponencial efectivo. Cada infusion entregada se contabiliza
    y decae con el tiempo.
    """

    action_duration_min: float = 300.0
    _events: deque = field(default_factory=deque, init=False, repr=False)

    def add(self, amount_uU: float, t_min: float) -> None:
        if amount_uU > 0:
            self._events.append((t_min, amount_uU))

    def value(self, t_min: float) -> float:
        # tau elegido para que a action_duration_min quede ~5% remanente.
        tau = self.action_duration_min / 3.0
        iob = 0.0
        keep = deque()
        for t0, amt in self._events:
            age = t_min - t0
            if age < 0:
                keep.append((t0, amt))
                continue
            remaining = amt * pow(2.718281828, -age / tau)
            if remaining > 1e-3:
                iob += remaining
                keep.append((t0, amt))
        self._events = keep
        return iob


@dataclass
class SafetySupervisor:
    """Supervisa y limita la orden de infusion del controlador."""

    limits: SafetyLimits = field(default_factory=SafetyLimits)
    iob: InsulinOnBoard = field(default_factory=InsulinOnBoard)
    dt_min: float = 5.0

    _last_command: float = field(default=0.0, init=False, repr=False)
    _suspended: bool = field(default=False, init=False, repr=False)

    def _predicted_glucose(
        self, glucose: float, rate_mgdl_min: Optional[float]
    ) -> float:
        if rate_mgdl_min is None:
            return glucose
        return glucose + rate_mgdl_min * self.limits.prediction_horizon_min

    def evaluate(
        self,
        requested_uU_min: float,
        glucose_mgdl: float,
        t_min: float,
        glucose_rate_mgdl_min: Optional[float] = None,
        sensor_age_min: float = 0.0,
    ) -> tuple[float, SafetyState]:
        """Devuelve (infusion_permitida, estado) tras aplicar salvaguardas.

        Parameters
        ----------
        requested_uU_min : orden del controlador [uU/min]
        glucose_mgdl : ultima glucosa valida [mg/dL]
        t_min : tiempo actual [min]
        glucose_rate_mgdl_min : pendiente estimada de glucosa [mg/dL/min]
        sensor_age_min : antiguedad del dato de glucosa [min]
        """
        lim = self.limits
        lo, hi = lim.glucose_valid_range_mgdl

        # 1) Falla de sensor: dato invalido o viejo -> suspender.
        invalid = not (lo <= glucose_mgdl <= hi)
        stale = sensor_age_min > lim.max_sensor_age_min
        if invalid or stale:
            self._last_command = 0.0
            return 0.0, SafetyState.SUSPENDED_FAULT

        # 2) Suspension por glucosa baja (reactiva).
        if glucose_mgdl <= lim.low_glucose_suspend_mgdl:
            self._suspended = True
        # 3) Suspension predictiva.
        predicted = self._predicted_glucose(glucose_mgdl, glucose_rate_mgdl_min)
        predicted_low = predicted <= lim.predicted_low_mgdl

        # Reanudacion: solo si la glucosa supera el umbral de reanudacion y no
        # hay prediccion de baja.
        if self._suspended and glucose_mgdl >= lim.resume_glucose_mgdl and not predicted_low:
            self._suspended = False

        if self._suspended:
            self._last_command = 0.0
            return 0.0, SafetyState.SUSPENDED_LOW
        if predicted_low:
            self._last_command = 0.0
            return 0.0, SafetyState.SUSPENDED_PREDICTED_LOW

        state = SafetyState.NORMAL
        allowed = max(requested_uU_min, 0.0)

        # 4) Tope por insulina activa: si IOB ya esta en el limite, no sumar.
        current_iob = self.iob.value(t_min)
        if current_iob >= lim.max_iob_uU:
            allowed = 0.0
            state = SafetyState.IOB_CAPPED
        else:
            # margen de IOB disponible expresado como dosis en este intervalo
            iob_room = lim.max_iob_uU - current_iob
            max_by_iob = iob_room / self.dt_min
            if allowed > max_by_iob:
                allowed = max_by_iob
                state = SafetyState.IOB_CAPPED

        # 5) Tope duro de tasa.
        if allowed > lim.max_infusion_uU_min:
            allowed = lim.max_infusion_uU_min
            state = SafetyState.DOSE_CAPPED if state is SafetyState.NORMAL else state

        # 6) Limitacion de velocidad de cambio.
        max_step = lim.max_delta_uU_min_per_min * self.dt_min
        if allowed - self._last_command > max_step:
            allowed = self._last_command + max_step
            state = SafetyState.RATE_LIMITED if state is SafetyState.NORMAL else state

        allowed = max(allowed, 0.0)
        self._last_command = allowed
        # Contabiliza la insulina efectivamente entregada en este intervalo.
        self.iob.add(allowed * self.dt_min, t_min)
        return allowed, state
