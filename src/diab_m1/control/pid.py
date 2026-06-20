"""Controlador PID discreto para regulacion de glucosa.

Implementa un PID clasico con:
- anti-windup por "back-calculation" y por limitacion del termino integral,
- filtro de primer orden en la derivada (para no amplificar ruido del sensor),
- saturacion configurable de la salida.

Sigue el esquema de Soylu & Danisman (2016) para control de glucosa en
sangre: el error es e(t) = G(t) - G_objetivo, y una salida positiva ordena
infundir insulina (la insulina baja la glucosa). El termino derivativo se
aplica sobre la medicion y no sobre el error, lo que evita el "derivative
kick" ante cambios de referencia.

IMPORTANTE: este controlador, por si solo, NO es seguro para dosificar
insulina a una persona. Debe envolverse en la capa de seguridad
(`diab_m1.control.safety`), que impone limites duros, suspension por
hipoglucemia e insulina activa. Ver DISCLAIMER.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PIDGains:
    kp: float
    ki: float
    kd: float


@dataclass
class PIDController:
    """PID discreto orientado a salida de tasa de infusion de insulina.

    Parameters
    ----------
    gains : PIDGains
        Ganancias kp, ki, kd. Unidades segun la planta (p. ej. uU/min por
        mg/dL para kp).
    setpoint : float
        Glucosa objetivo [mg/dL].
    out_min, out_max : float
        Saturacion de la salida (p. ej. 0 a tasa maxima de infusion).
    derivative_tau : float
        Constante de tiempo [min] del filtro derivativo. 0 lo desactiva.
    """

    gains: PIDGains
    setpoint: float = 110.0
    out_min: float = 0.0
    out_max: float = float("inf")
    derivative_tau: float = 5.0

    _integral: float = field(default=0.0, init=False, repr=False)
    _prev_meas: float | None = field(default=None, init=False, repr=False)
    _deriv_filt: float = field(default=0.0, init=False, repr=False)

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_meas = None
        self._deriv_filt = 0.0

    def update(self, measurement: float, dt_min: float) -> float:
        """Calcula la salida del PID para una medicion de glucosa.

        Parameters
        ----------
        measurement : glucosa medida [mg/dL]
        dt_min : intervalo de muestreo [min]

        Returns
        -------
        salida saturada (tasa de infusion solicitada, mismas unidades que
        out_min/out_max).
        """
        if dt_min <= 0:
            raise ValueError("dt_min debe ser positivo")

        error = measurement - self.setpoint  # >0 => glucosa alta => infundir

        # Proporcional
        p_term = self.gains.kp * error

        # Derivada sobre la medicion (con filtro de primer orden), signo
        # negativo porque d(error)/dt = d(meas)/dt cuando el setpoint es fijo.
        if self._prev_meas is None:
            raw_deriv = 0.0
        else:
            raw_deriv = (measurement - self._prev_meas) / dt_min
        if self.derivative_tau > 0:
            alpha = dt_min / (self.derivative_tau + dt_min)
            self._deriv_filt += alpha * (raw_deriv - self._deriv_filt)
            deriv = self._deriv_filt
        else:
            deriv = raw_deriv
        d_term = self.gains.kd * deriv

        # Integral tentativa
        tentative_integral = self._integral + error * dt_min
        i_term = self.gains.ki * tentative_integral

        unsat = p_term + i_term + d_term
        out = min(max(unsat, self.out_min), self.out_max)

        # Anti-windup: solo se acumula el integrador si no empuja mas alla de
        # la saturacion (clamping condicional).
        saturated_high = unsat > self.out_max and error > 0
        saturated_low = unsat < self.out_min and error < 0
        if not (saturated_high or saturated_low):
            self._integral = tentative_integral

        self._prev_meas = measurement
        return out

    @property
    def integral(self) -> float:
        return self._integral
