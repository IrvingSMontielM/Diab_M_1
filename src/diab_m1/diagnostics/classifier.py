"""Clasificacion de estado glucemico segun criterios diagnosticos vigentes.

Implementa los puntos de corte para tamizaje y diagnostico de diabetes
mellitus a partir de los analisis de sangre estandar:

- Glucosa plasmatica en ayuno (FPG), >= 8 h de ayuno.
- HbA1c (NGSP %).
- Glucosa a las 2 h en la curva de tolerancia oral a la glucosa (CTGO/OGTT,
  carga de 75 g).
- Glucosa plasmatica casual (random) con sintomas clasicos.

Fuentes de los puntos de corte:
  * American Diabetes Association, "Standards of Care in Diabetes"
    (clasificacion y diagnostico, Seccion 2). Diabetes Care.
  * World Health Organization / IDF, "Definition and diagnosis of diabetes
    mellitus and intermediate hyperglycaemia".
  * NOM-015-SSA2-2010, "Para la prevencion, tratamiento y control de la
    diabetes mellitus" (Mexico).

Diferencia relevante ADA vs OMS: el limite inferior de glucosa alterada en
ayuno (IFG) es 100 mg/dL para la ADA y 110 mg/dL para la OMS. El parametro
`criteria` permite seleccionar el marco.

ADVERTENCIA CLINICA
-------------------
Este modulo es una herramienta de apoyo a la decision y fines educativos /
de investigacion. NO sustituye el juicio de un profesional de la salud ni
constituye un diagnostico. Salvo hiperglucemia inequivoca con sintomas, el
diagnostico de diabetes requiere CONFIRMACION con una segunda prueba
anormal (la misma prueba repetida o dos pruebas distintas), tomada en un
dia diferente. Estas reglas estan codificadas pero su aplicacion clinica
corresponde al medico tratante.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..units import mmoll_to_mgdl


class GlycemicStatus(str, Enum):
    NORMAL = "normal"
    PREDIABETES = "prediabetes"
    DIABETES = "diabetes"
    INDETERMINATE = "indeterminado"


class Criteria(str, Enum):
    ADA = "ADA"
    WHO = "OMS"


# Puntos de corte en mg/dL y % (HbA1c). Ver fuentes en el docstring del modulo.
_THRESHOLDS = {
    Criteria.ADA: {
        "fpg_prediabetes_low": 100.0,   # mg/dL, IFG (ADA)
        "fpg_diabetes": 126.0,          # mg/dL
        "ogtt_prediabetes_low": 140.0,  # mg/dL, IGT
        "ogtt_diabetes": 200.0,         # mg/dL
        "a1c_prediabetes_low": 5.7,     # %
        "a1c_diabetes": 6.5,            # %
        "random_diabetes": 200.0,       # mg/dL (con sintomas)
    },
    Criteria.WHO: {
        "fpg_prediabetes_low": 110.0,   # mg/dL, IFG (OMS)
        "fpg_diabetes": 126.0,
        "ogtt_prediabetes_low": 140.0,
        "ogtt_diabetes": 200.0,
        "a1c_prediabetes_low": 5.7,
        "a1c_diabetes": 6.5,
        "random_diabetes": 200.0,
    },
}


@dataclass
class TestResult:
    """Resultado de una sola prueba y su clasificacion."""

    test: str
    value: float
    unit: str
    status: GlycemicStatus
    threshold_note: str


@dataclass
class DiagnosticReport:
    """Interpretacion agregada de las pruebas disponibles."""

    criteria: Criteria
    per_test: list[TestResult]
    overall: GlycemicStatus
    requires_confirmation: bool
    rationale: str

    def summary(self) -> str:
        lines = [f"Criterio aplicado: {self.criteria.value}"]
        for r in self.per_test:
            lines.append(
                f"  - {r.test}: {r.value:g} {r.unit} -> {r.status.value} "
                f"({r.threshold_note})"
            )
        lines.append(f"Interpretacion global: {self.overall.value}")
        if self.requires_confirmation:
            lines.append(
                "  Requiere CONFIRMACION con una segunda prueba anormal en "
                "dia distinto."
            )
        lines.append(f"Justificacion: {self.rationale}")
        lines.append(
            "Apoyo a la decision; no es diagnostico. Confirmar con un "
            "profesional de la salud."
        )
        return "\n".join(lines)


def _classify_fpg(value: float, t: dict) -> tuple[GlycemicStatus, str]:
    if value >= t["fpg_diabetes"]:
        return GlycemicStatus.DIABETES, f">= {t['fpg_diabetes']:g} mg/dL"
    if value >= t["fpg_prediabetes_low"]:
        return (
            GlycemicStatus.PREDIABETES,
            f"{t['fpg_prediabetes_low']:g}-125 mg/dL (glucosa alterada en ayuno)",
        )
    return GlycemicStatus.NORMAL, f"< {t['fpg_prediabetes_low']:g} mg/dL"


def _classify_ogtt(value: float, t: dict) -> tuple[GlycemicStatus, str]:
    if value >= t["ogtt_diabetes"]:
        return GlycemicStatus.DIABETES, f">= {t['ogtt_diabetes']:g} mg/dL a 2 h"
    if value >= t["ogtt_prediabetes_low"]:
        return (
            GlycemicStatus.PREDIABETES,
            f"{t['ogtt_prediabetes_low']:g}-199 mg/dL (intolerancia a la glucosa)",
        )
    return GlycemicStatus.NORMAL, f"< {t['ogtt_prediabetes_low']:g} mg/dL a 2 h"


def _classify_a1c(value: float, t: dict) -> tuple[GlycemicStatus, str]:
    if value >= t["a1c_diabetes"]:
        return GlycemicStatus.DIABETES, f">= {t['a1c_diabetes']:g} %"
    if value >= t["a1c_prediabetes_low"]:
        return GlycemicStatus.PREDIABETES, f"{t['a1c_prediabetes_low']:g}-6.4 %"
    return GlycemicStatus.NORMAL, f"< {t['a1c_prediabetes_low']:g} %"


_SEVERITY = {
    GlycemicStatus.NORMAL: 0,
    GlycemicStatus.PREDIABETES: 1,
    GlycemicStatus.DIABETES: 2,
    GlycemicStatus.INDETERMINATE: -1,
}


def classify(
    fpg_mg_dl: Optional[float] = None,
    a1c_percent: Optional[float] = None,
    ogtt_2h_mg_dl: Optional[float] = None,
    random_glucose_mg_dl: Optional[float] = None,
    classic_symptoms: bool = False,
    criteria: Criteria = Criteria.ADA,
    units: str = "mg/dL",
) -> DiagnosticReport:
    """Clasifica el estado glucemico a partir de una o varias pruebas.

    Parameters
    ----------
    fpg_mg_dl, a1c_percent, ogtt_2h_mg_dl, random_glucose_mg_dl
        Valores de las pruebas. Cualquiera puede ser None si no se dispone.
        HbA1c siempre en %. Glucosas en `units`.
    classic_symptoms
        True si hay poliuria, polidipsia, perdida de peso inexplicada, etc.
        Una glucosa casual >= 200 mg/dL con sintomas es diagnostica sin
        confirmacion.
    criteria
        Marco de puntos de corte (ADA u OMS).
    units
        'mg/dL' (por defecto) o 'mmol/L' para las glucosas (no para A1c).

    Returns
    -------
    DiagnosticReport
    """
    t = _THRESHOLDS[criteria]

    def to_mgdl(v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        if units == "mmol/L":
            return mmoll_to_mgdl(v)
        if units == "mg/dL":
            return v
        raise ValueError("units debe ser 'mg/dL' o 'mmol/L'")

    fpg = to_mgdl(fpg_mg_dl)
    ogtt = to_mgdl(ogtt_2h_mg_dl)
    rnd = to_mgdl(random_glucose_mg_dl)

    per_test: list[TestResult] = []

    if fpg is not None:
        st, note = _classify_fpg(fpg, t)
        per_test.append(TestResult("Glucosa en ayuno", fpg_mg_dl, units, st, note))
    if a1c_percent is not None:
        st, note = _classify_a1c(a1c_percent, t)
        per_test.append(TestResult("HbA1c", a1c_percent, "%", st, note))
    if ogtt is not None:
        st, note = _classify_ogtt(ogtt, t)
        per_test.append(TestResult("CTGO 2 h", ogtt_2h_mg_dl, units, st, note))

    # Hiperglucemia inequivoca: glucosa casual >= 200 con sintomas clasicos.
    unequivocal = False
    if rnd is not None:
        if rnd >= t["random_diabetes"] and classic_symptoms:
            unequivocal = True
            per_test.append(
                TestResult(
                    "Glucosa casual + sintomas",
                    random_glucose_mg_dl,
                    units,
                    GlycemicStatus.DIABETES,
                    f">= {t['random_diabetes']:g} mg/dL con sintomas (diagnostica)",
                )
            )
        else:
            note = (
                f">= {t['random_diabetes']:g} mg/dL pero sin sintomas: requiere "
                "prueba estandar"
                if rnd >= t["random_diabetes"]
                else f"< {t['random_diabetes']:g} mg/dL"
            )
            st = (
                GlycemicStatus.DIABETES
                if rnd >= t["random_diabetes"]
                else GlycemicStatus.NORMAL
            )
            per_test.append(
                TestResult("Glucosa casual", random_glucose_mg_dl, units, st, note)
            )

    if not per_test:
        return DiagnosticReport(
            criteria=criteria,
            per_test=[],
            overall=GlycemicStatus.INDETERMINATE,
            requires_confirmation=False,
            rationale="No se proporciono ninguna prueba.",
        )

    overall = max((r.status for r in per_test), key=lambda s: _SEVERITY[s])

    n_diabetes = sum(1 for r in per_test if r.status is GlycemicStatus.DIABETES)
    requires_confirmation = False
    rationale = ""

    if overall is GlycemicStatus.DIABETES:
        if unequivocal:
            requires_confirmation = False
            rationale = (
                "Hiperglucemia inequivoca (glucosa casual alta con sintomas): "
                "no requiere confirmacion."
            )
        elif n_diabetes >= 2:
            requires_confirmation = False
            rationale = (
                "Dos o mas pruebas distintas en rango diabetico de forma "
                "concordante: criterio diagnostico cumplido."
            )
        else:
            requires_confirmation = True
            rationale = (
                "Una sola prueba en rango diabetico: la ADA y la OMS exigen "
                "confirmar con una segunda prueba anormal en dia distinto antes "
                "de establecer el diagnostico."
            )
    elif overall is GlycemicStatus.PREDIABETES:
        rationale = (
            "Resultado(s) en categoria de mayor riesgo (prediabetes / "
            "glucosa alterada). Indica vigilancia y modificacion del estilo "
            "de vida."
        )
    else:
        rationale = "Todas las pruebas dentro de rango normal."

    return DiagnosticReport(
        criteria=criteria,
        per_test=per_test,
        overall=overall,
        requires_confirmation=requires_confirmation,
        rationale=rationale,
    )
