"""Conversiones de unidades clinicas para glucosa e insulina.

Todas las conversiones siguen referencias internacionales estandar:

- Glucosa mg/dL <-> mmol/L: factor 18.0182 (peso molecular de la glucosa,
  180.16 g/mol). Es la convencion adoptada por la IFCC y la mayoria de la
  literatura. Mexico (NOM-015-SSA2-2010) y EE.UU. reportan en mg/dL; gran
  parte de la literatura europea usa mmol/L.

- HbA1c NGSP (%) <-> IFCC (mmol/mol): ecuacion maestra NGSP/IFCC
  IFCC = 10.929 * (NGSP - 2.15).

- HbA1c (%) <-> glucosa media estimada (eAG): estudio ADAG
  (Nathan et al., Diabetes Care 2008): eAG_mg_dL = 28.7 * A1c - 46.7.

Estas funciones son utilitarias y no constituyen interpretacion clinica.
"""

from __future__ import annotations

# Factor de conversion glucosa: 1 mmol/L = 18.0182 mg/dL
MG_DL_PER_MMOL_L: float = 18.0182


def mgdl_to_mmoll(mg_dl: float) -> float:
    """Convierte glucosa de mg/dL a mmol/L."""
    return mg_dl / MG_DL_PER_MMOL_L


def mmoll_to_mgdl(mmol_l: float) -> float:
    """Convierte glucosa de mmol/L a mg/dL."""
    return mmol_l * MG_DL_PER_MMOL_L


def a1c_to_ifcc(a1c_percent: float) -> float:
    """Convierte HbA1c NGSP (%) a IFCC (mmol/mol)."""
    return 10.929 * (a1c_percent - 2.15)


def ifcc_to_a1c(ifcc_mmol_mol: float) -> float:
    """Convierte HbA1c IFCC (mmol/mol) a NGSP (%)."""
    return ifcc_mmol_mol / 10.929 + 2.15


def a1c_to_eag_mgdl(a1c_percent: float) -> float:
    """Glucosa media estimada (eAG) en mg/dL a partir de HbA1c (%).

    Ecuacion ADAG: eAG = 28.7 * A1c - 46.7. Valida aproximadamente
    para A1c entre 5% y 12%.
    """
    return 28.7 * a1c_percent - 46.7


def a1c_to_eag_mmoll(a1c_percent: float) -> float:
    """Glucosa media estimada (eAG) en mmol/L a partir de HbA1c (%)."""
    return mgdl_to_mmoll(a1c_to_eag_mgdl(a1c_percent))


def eag_mgdl_to_a1c(eag_mg_dl: float) -> float:
    """HbA1c (%) estimada a partir de la glucosa media (eAG) en mg/dL."""
    return (eag_mg_dl + 46.7) / 28.7
