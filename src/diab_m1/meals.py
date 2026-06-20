"""Generador de perturbaciones por ingesta (comidas).

Reproduce el esquema de la propuesta: tres comidas diarias modeladas como
pulsos de aparicion de glucosa exogena. Por defecto 40 g a las 07:00,
60 g a las 12:00 y 60 g a las 17:00, cada una distribuida en una ventana de
30 min, igual que en el modelo de Simulink original.

Dos representaciones:

- `pulse_rate(t)`: tasa de infusion de glucosa tipo "pulso rectangular",
  apropiada para el modelo de Stolwijk-Hardy (entrada u(t) en mg/h o mg/s).
- `ra_appearance(t)`: tasa de aparicion de glucosa con un perfil suave
  (gamma) mas realista de absorcion intestinal, apropiada para modelos tipo
  Bergman donde Ra(t) entra en mg/dL/min.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Meal:
    """Una comida: hora de inicio (h), gramos de carbohidrato, duracion (h)."""

    start_h: float
    grams: float
    duration_h: float = 0.5


DEFAULT_MEALS: tuple[Meal, ...] = (
    Meal(start_h=7.0, grams=40.0),    # desayuno
    Meal(start_h=12.0, grams=60.0),   # comida
    Meal(start_h=17.0, grams=60.0),   # cena
)


@dataclass
class MealSchedule:
    """Conjunto de comidas del dia y conversores a tasa de glucosa."""

    meals: tuple[Meal, ...] = field(default_factory=lambda: DEFAULT_MEALS)
    glucose_mg_per_g: float = 1000.0  # 1 g de carbohidrato -> 1000 mg de glucosa

    def pulse_rate_mg_per_h(self, t_h: float) -> float:
        """Tasa rectangular de glucosa exogena en mg/h en el instante t_h."""
        rate = 0.0
        for m in self.meals:
            if m.start_h <= t_h < m.start_h + m.duration_h:
                total_mg = m.grams * self.glucose_mg_per_g
                rate += total_mg / m.duration_h
        return rate

    def pulse_rate_mg_per_s(self, t_s: float) -> float:
        """Igual que `pulse_rate_mg_per_h` pero con el tiempo en segundos.

        Equivale a la ganancia 1/3600 aplicada en el modelo de Simulink.
        """
        return self.pulse_rate_mg_per_h(t_s / 3600.0) / 3600.0

    def ra_mass_mg_per_h(
        self,
        t_h: float,
        bioavailability: float = 0.9,
        peak_h: float = 0.75,
    ) -> float:
        """Tasa de aparicion de glucosa en MASA [mg/h] con absorcion gamma.

        Perfil de absorcion intestinal mas realista que el pulso rectangular:
        subida y bajada suaves con pico a `peak_h` horas. La integral en el
        tiempo de cada comida es grams*1000*bioavailability (mg). Apropiada
        como entrada u(t) [mg/h] del modelo de Stolwijk-Hardy.
        """
        from math import gamma as _gamma

        k = 2.0
        theta = peak_h / (k - 1.0)  # el pico de la gamma(k) cae en (k-1)*theta
        rate = 0.0
        for m in self.meals:
            tau = t_h - m.start_h
            if tau <= 0:
                continue
            dose_mg = m.grams * self.glucose_mg_per_g * bioavailability
            density = (tau ** (k - 1) * np.exp(-tau / theta)) / (
                theta ** k * _gamma(k)
            )
            rate += dose_mg * density
        return rate

    def ra_appearance_mg_per_dl_min(
        self,
        t_min: float,
        vg_dl: float = 117.0,
        bioavailability: float = 0.8,
        peak_min: float = 40.0,
    ) -> float:
        """Tasa de aparicion de glucosa Ra(t) en mg/dL/min para modelos minimos.

        Usa un perfil gamma por comida (subida y bajada suaves) con pico a
        `peak_min` minutos. `vg_dl` es el volumen de distribucion de glucosa
        en dL (por defecto ~11.7 L para un adulto de ~70 kg).
        """
        ra_mg_min = 0.0
        k = 2.0  # forma de la gamma (k=2 da un pico unico suave)
        theta = peak_min / k  # escala para que el pico caiga en peak_min
        for m in self.meals:
            tau = (t_min - m.start_h * 60.0)
            if tau <= 0:
                continue
            dose_mg = m.grams * self.glucose_mg_per_g * bioavailability
            # densidad gamma normalizada (integral = 1 en mg)
            gamma = (tau ** (k - 1) * np.exp(-tau / theta)) / (
                theta ** k * _gamma_factorial(k)
            )
            ra_mg_min += dose_mg * gamma
        return ra_mg_min / vg_dl


def _gamma_factorial(k: float) -> float:
    """(k-1)! para k entero pequeno; aqui k=2 -> 1."""
    from math import gamma as _g

    return _g(k)


def meal_carbs_grid(schedule: MealSchedule, t_h: np.ndarray) -> np.ndarray:
    """Vectoriza `pulse_rate_mg_per_h` sobre un arreglo de tiempos (h)."""
    return np.array([schedule.pulse_rate_mg_per_h(float(t)) for t in t_h])
