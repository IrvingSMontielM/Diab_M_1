"""Ejemplo 02: lazo cerrado PID + supervisor de seguridad (paciente DM1).

Controla la glucosa de un paciente virtual DM1 (modelo minimo de Bergman) ante
las tres comidas del dia. El controlador PID calcula la tasa de infusion de
insulina y un supervisor de seguridad la limita imitando las salvaguardas de
un pancreas artificial real: suspension por hipoglucemia (LGS), suspension
predictiva (PLGS), tope de insulina activa (IOB), tope duro de dosis y limite
de velocidad de cambio.

Compara el lazo cerrado contra el lazo abierto (solo basal) y reporta el tiempo
en rango (TIR) 70-180 mg/dL.

Ejecutar:
    PYTHONPATH=src python3 examples/02_closed_loop_pid.py
Genera:
    examples/figures/02_closed_loop.png
"""

from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from diab_m1.control.pid import PIDController, PIDGains  # noqa: E402
from diab_m1.control.safety import (  # noqa: E402
    SafetyLimits,
    SafetyState,
    SafetySupervisor,
)
from diab_m1.meals import MealSchedule  # noqa: E402
from diab_m1.models.bergman import BergmanParams, basal_insulin_infusion  # noqa: E402
from diab_m1.models.bergman import _rhs as bergman_rhs  # noqa: E402
from diab_m1.signal.cgm import clarke_zone_distribution  # noqa: E402

FIG_DIR = Path(__file__).parent / "figures"
FIG_DIR.mkdir(exist_ok=True)


def time_in_range(glucose, lo=70.0, hi=180.0):
    g = np.asarray(glucose)
    return 100.0 * np.mean((g >= lo) & (g <= hi))


def run():
    from scipy.integrate import solve_ivp

    p = BergmanParams()
    sched = MealSchedule()
    dt = 5.0  # min, periodo de muestreo del CGM/controlador
    minutes = 24 * 60.0
    n_steps = int(minutes / dt)

    def ra(t_min):
        return sched.ra_appearance_mg_per_dl_min(t_min % minutes)

    # --- Configuracion verificada del controlador y la seguridad ---
    pid = PIDController(
        gains=PIDGains(kp=4000.0, ki=8.0, kd=80000.0),
        setpoint=120.0,
        out_min=0.0,
        out_max=200000.0,
        derivative_tau=15.0,
    )
    limits = SafetyLimits(
        predicted_low_mgdl=80.0,
        prediction_horizon_min=30.0,
        low_glucose_suspend_mgdl=70.0,
        resume_glucose_mgdl=80.0,
    )
    supervisor = SafetySupervisor(limits=limits, dt_min=dt)

    # Estado del paciente: [G, X, I]
    state = np.array([p.gb, 0.0, p.ib])
    t = 0.0
    prev_g = p.gb

    log = {"t": [], "g": [], "u": [], "state": []}
    for _ in range(n_steps):
        g_meas = state[0]
        rate = (g_meas - prev_g) / dt  # mg/dL/min
        prev_g = g_meas

        requested = pid.update(g_meas, dt_min=dt)
        allowed, sstate = supervisor.evaluate(
            requested_uU_min=requested,
            glucose_mgdl=g_meas,
            t_min=t,
            glucose_rate_mgdl_min=rate,
            sensor_age_min=0.0,
        )
        supervisor.iob.add(allowed * dt, t)

        sol = solve_ivp(
            bergman_rhs,
            (t, t + dt),
            state,
            args=(p, ra, lambda _t: allowed),
            max_step=1.0,
            rtol=1e-6,
            atol=1e-9,
        )
        state = sol.y[:, -1]
        t += dt
        log["t"].append(t / 60.0)
        log["g"].append(g_meas)
        log["u"].append(allowed)
        log["state"].append(sstate)

    # --- Lazo abierto de referencia (solo basal nominal) ---
    u_basal = basal_insulin_infusion(p)
    sol_ol = solve_ivp(
        bergman_rhs,
        (0.0, minutes),
        [p.gb, 0.0, p.ib],
        args=(p, ra, lambda _t: u_basal),
        max_step=1.0,
        rtol=1e-6,
        atol=1e-9,
        dense_output=True,
    )
    t_ol = np.arange(0, minutes, dt)
    g_ol = sol_ol.sol(t_ol)[0]

    g_cl = np.array(log["g"])
    tir_cl = time_in_range(g_cl)
    tir_ol = time_in_range(g_ol)
    n_susp = sum(
        1
        for s in log["state"]
        if s
        in (
            SafetyState.SUSPENDED_LOW,
            SafetyState.SUSPENDED_PREDICTED_LOW,
            SafetyState.SUSPENDED_FAULT,
        )
    )

    print("Resultados del lazo cerrado (PID + seguridad):")
    print(f"  glucosa min/media/max : {g_cl.min():.0f} / {g_cl.mean():.0f} / "
          f"{g_cl.max():.0f} mg/dL")
    print(f"  TIR 70-180            : {tir_cl:.1f} %")
    print(f"  tiempo < 70 mg/dL     : {100.0*np.mean(g_cl<70):.1f} %")
    print(f"  pasos suspendidos     : {n_susp} de {n_steps}")
    print("Lazo abierto (solo basal):")
    print(f"  glucosa min/media/max : {g_ol.min():.0f} / {g_ol.mean():.0f} / "
          f"{g_ol.max():.0f} mg/dL")
    print(f"  TIR 70-180            : {tir_ol:.1f} %")

    dist = clarke_zone_distribution(measured_mgdl=g_cl, reference_mgdl=g_cl)
    print(f"  zonas Clarke (auto)   : {dist}")

    # --- Figura ---
    fig, (ax_g, ax_u) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    ax_g.axhspan(70, 180, color="#e8f5e9", zorder=0, label="rango 70-180")
    ax_g.plot(log["t"], g_cl, color="#c33", lw=1.8, label="lazo cerrado PID")
    ax_g.plot(t_ol / 60.0, g_ol, color="#999", lw=1.4, ls="--",
              label="lazo abierto (basal)")
    ax_g.axhline(70, color="#e53935", lw=0.8, ls=":")
    ax_g.set_ylabel("Glucosa [mg/dL]")
    ax_g.set_title("Lazo cerrado PID + supervisor de seguridad (DM1, Bergman)")
    ax_g.legend(loc="upper right")
    ax_g.grid(alpha=0.25)

    u_arr = np.array(log["u"]) / 1000.0  # mU/min
    ax_u.step(log["t"], u_arr, where="post", color="#36c", lw=1.4,
              label="infusion permitida")
    susp_t = [tt for tt, s in zip(log["t"], log["state"])
              if s in (SafetyState.SUSPENDED_LOW,
                       SafetyState.SUSPENDED_PREDICTED_LOW)]
    for st in susp_t:
        ax_u.axvline(st, color="#fb8c00", alpha=0.35, lw=2)
    ax_u.set_ylabel("Infusion [mU/min]")
    ax_u.set_xlabel("Tiempo [h]  (naranja = suspension por seguridad)")
    ax_u.legend(loc="upper right")
    ax_u.grid(alpha=0.25)
    fig.tight_layout()
    out_path = FIG_DIR / "02_closed_loop.png"
    fig.savefig(out_path, dpi=130)
    print(f"\nFigura guardada en: {out_path}")


if __name__ == "__main__":
    run()
