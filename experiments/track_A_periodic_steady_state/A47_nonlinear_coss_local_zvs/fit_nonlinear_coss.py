"""Fit a smooth, differentiable, integrable Coss(V) model to the digitized
GS61008T Figure-7 points (gs61008t_coss_digitized_raw.csv), and derive the
closed-form charge function Q(V) used by the nonlinear LTspice capacitor in
A47's stage-1/stage-2 netlists.

Functional form (a standard "Hill"/generalized-logistic GaN-Coss shape,
chosen -- among several tried, see BOUNDARY.md -- specifically because it
has a clean, closed-form, exactly integrable Q(V) using only atan(), which
this project's build scripts hand to LTspice's `B<name> n1 n2 I=ddt(Q(V))`
nonlinear-capacitor idiom):

    Coss(V) = C_FLOOR + A_COSS / (1 + (V / V_KNEE)^2)

    Q(V) = integral_0^V Coss(v) dv
         = C_FLOOR*V + A_COSS*V_KNEE*atan(V / V_KNEE)

Both Coss(V) (even) and Q(V) (odd) are smooth for all real V, including
V<0, which only ever occurs in this project's simulations as a small
overshoot right at a ZVS crossing; extending the fitted curve symmetrically
through V=0 is the least-arbitrary continuation available and is declared
as an explicit idealization in BOUNDARY.md (the datasheet only characterizes
V>=0).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

HERE = Path(__file__).resolve().parent
RAW_CSV = HERE / "gs61008t_coss_digitized_raw.csv"
OUT_JSON = HERE / "fit_results.json"

# Datasheet-printed reference values (EXTERNAL_DEVICE_DATA, GS61008T Rev
# 200402), used only to CROSS-CHECK the digitization/fit, never as fit
# inputs themselves.
REF_COSS_50V_PF = 250.0
REF_CO_TR_PF = 385.0
REF_CO_ER_PF = 302.0


def load_points() -> tuple[np.ndarray, np.ndarray]:
    V, C = [], []
    with RAW_CSV.open() as f:
        for row in csv.DictReader(f):
            V.append(float(row["Vds_V"]))
            C.append(float(row["Coss_pF"]))
    order = np.argsort(V)
    return np.array(V)[order], np.array(C)[order]


def coss_model(V: np.ndarray, c_floor: float, a_coss: float, v_knee: float) -> np.ndarray:
    return c_floor + a_coss / (1.0 + (V / v_knee) ** 2)


def fit() -> dict:
    V, C = load_points()

    def log_model(V, c_floor, a_coss, v_knee):
        return np.log(coss_model(V, c_floor, a_coss, v_knee))

    p0 = [200.0, 500.0, 15.0]
    bounds = ([100.0, 50.0, 0.5], [300.0, 3000.0, 80.0])
    popt, pcov = curve_fit(log_model, V, np.log(C), p0=p0, bounds=bounds, maxfev=100000)
    c_floor, a_coss, v_knee = (float(x) for x in popt)
    perr = np.sqrt(np.diag(pcov))

    pred = coss_model(V, *popt)
    resid = C - pred
    rmse_pF = float(np.sqrt(np.mean(resid**2)))
    r2 = float(1.0 - np.sum(resid**2) / np.sum((C - np.mean(C)) ** 2))
    max_rel_pct = float(np.max(np.abs(resid / C)) * 100.0)
    mean_rel_pct = float(np.mean(np.abs(resid / C)) * 100.0)
    max_rel_at_v = float(V[np.argmax(np.abs(resid / C))])

    # Cross-check the FIT (not just the raw digitized points) against the
    # three datasheet-printed reference numbers.
    v50 = np.array([50.0])
    coss_50 = float(coss_model(v50, *popt)[0])

    def Q(V):
        return c_floor * V + a_coss * v_knee * np.arctan(V / v_knee)

    q50 = Q(50.0)
    co_tr_fit = q50 / 50.0

    def E(V):
        return c_floor * V**2 / 2.0 + a_coss * v_knee**2 / 2.0 * np.log(1.0 + (V / v_knee) ** 2)

    e50 = E(50.0)
    co_er_fit = 2.0 * e50 / (50.0**2)

    results = {
        "n_points": int(len(V)),
        "v_range": [float(V.min()), float(V.max())],
        "model": "Coss(V) = C_FLOOR + A_COSS / (1 + (V/V_KNEE)^2)",
        "params": {
            "C_FLOOR_pF": c_floor,
            "A_COSS_pF": a_coss,
            "V_KNEE_V": v_knee,
        },
        "param_1sigma": {
            "C_FLOOR_pF": float(perr[0]),
            "A_COSS_pF": float(perr[1]),
            "V_KNEE_V": float(perr[2]),
        },
        "fit_quality": {
            "rmse_pF": rmse_pF,
            "R2": r2,
            "max_rel_error_pct": max_rel_pct,
            "max_rel_error_at_V": max_rel_at_v,
            "mean_rel_error_pct": mean_rel_pct,
        },
        "datasheet_crosscheck": {
            "Coss_at_50V_fit_pF": coss_50,
            "Coss_at_50V_datasheet_pF": REF_COSS_50V_PF,
            "Coss_at_50V_rel_error_pct": (coss_50 - REF_COSS_50V_PF) / REF_COSS_50V_PF * 100.0,
            "CO_TR_0_50V_fit_pF": co_tr_fit,
            "CO_TR_0_50V_datasheet_pF": REF_CO_TR_PF,
            "CO_TR_rel_error_pct": (co_tr_fit - REF_CO_TR_PF) / REF_CO_TR_PF * 100.0,
            "CO_ER_0_50V_fit_pF": co_er_fit,
            "CO_ER_0_50V_datasheet_pF": REF_CO_ER_PF,
            "CO_ER_rel_error_pct": (co_er_fit - REF_CO_ER_PF) / REF_CO_ER_PF * 100.0,
        },
        "Q_of_V_closed_form": (
            "Q(V) = C_FLOOR*V + A_COSS*V_KNEE*atan(V/V_KNEE)   "
            "[pF*V units above; multiply by 1e-12 for Farads*Volts=Coulombs]"
        ),
    }
    return results


def main() -> None:
    results = fit()
    OUT_JSON.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
