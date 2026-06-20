"""Ejemplo 01: reproduccion de los tres escenarios del modelo Stolwijk-Hardy.

Reproduce la respuesta glucosa-insulina de 24 h para persona sana, DM1 y DM2
ante las tres comidas del dia (40 g, 60 g, 60 g), tal como plantea el PDF de
la Actividad 4. Usa absorcion intestinal tipo gamma (mas realista que el pulso
rectangular del Simulink original) como entrada exogena u(t) [mg/h].

Ejecutar:
    PYTHONPATH=src python3 examples/01_simulate_scenarios.py
Genera:
    examples/figures/01_scenarios.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from diab_m1.meals import MealSchedule  # noqa: E402
from diab_m1.models.stolwijk_hardy import (  # noqa: E402
    dm1_params,
    dm2_params,
    equilibrium,
    healthy_params,
    simulate,
)

FIG_DIR = Path(__file__).parent / "figures"
FIG_DIR.mkdir(exist_ok=True)


def run():
    sched = MealSchedule()

    def u_glucose(t_h: float) -> float:
        # entrada periodica de 24 h en mg/h
        return sched.ra_mass_mg_per_h(t_h % 24.0)

    scenarios = {
        "Sano": healthy_params(),
        "DM2": dm2_params(),
        "DM1": dm1_params(),
    }

    fig, (ax_g, ax_i) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    colors = {"Sano": "#2a7", "DM1": "#c33", "DM2": "#36c"}
    styles = {"Sano": "-", "DM1": "--", "DM2": "-"}

    print("Escenario   basal_glu[mg/dL]  pico_glu[mg/dL]  basal_ins[mU/mL]")
    print("-" * 64)
    for name, p in scenarios.items():
        x0, y0 = equilibrium(p)
        out = simulate(p, u_glucose=u_glucose, hours=24.0)
        g = out["glucose_mgdl"]
        ax_g.plot(out["t_h"], g, label=name, color=colors[name],
                  ls=styles[name], lw=1.8)
        ax_i.plot(out["t_h"], out["insulin_muml"], label=name,
                  color=colors[name], ls=styles[name], lw=1.8)
        print(f"{name:<10}  {x0*100:>14.1f}  {g.max():>15.1f}  {y0:>16.4f}")

    for ax in (ax_g, ax_i):
        for h in (7, 12, 17):
            ax.axvline(h, color="0.8", ls="--", lw=0.8)
        ax.legend(loc="upper right")
        ax.grid(alpha=0.25)
    ax_g.axhspan(70, 180, color="0.9", zorder=0)  # rango objetivo
    ax_g.set_ylabel("Glucosa [mg/dL]")
    ax_i.set_ylabel("Insulina [mU/mL]")
    ax_i.set_xlabel("Tiempo [h]  (lineas: comidas 07:00, 12:00, 17:00)")
    ax_g.set_title("Stolwijk-Hardy (Khoo 2018): respuesta a 3 comidas, 24 h")
    fig.tight_layout()
    out_path = FIG_DIR / "01_scenarios.png"
    fig.savefig(out_path, dpi=130)
    print(f"\nFigura guardada en: {out_path}")


if __name__ == "__main__":
    run()
