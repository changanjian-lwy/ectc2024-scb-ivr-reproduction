"""Sensitivity branch: release three phase-specific on-times.

The extra controller freedom is not stated by P25 and is not promoted into the
baseline.  It diagnoses whether two flying-capacitor balance equations require
more than one common timing degree of freedom.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from p25_native_fixed_slot_ring import VIN, SLOT, event_ring, CFLY
from strict_joint_p25_fit import (
    TARGET_MODULE_CURRENT_A, SCALE,
    V_RETURN_TOL, I_RETURN_TOL, SPACING_TOL_NS, PEAK_TOL_A,
    MODULE_CURRENT_TOL_A,
)


HERE = Path(__file__).parent
OUT = HERE / "numerical_runs/06_per_phase_ton_sensitivity"
ZERO_VALLEY_PEAK = 2.0 * 200.0 / 9.0


def decode(q):
    alpha = q[7]
    peak = ZERO_VALLEY_PEAK/(1-alpha)
    return (np.r_[VIN,q[:7]], alpha, peak, alpha*peak,
            q[8]*1e-9, np.asarray(q[9:12])*1e-9)


def raw(q):
    initial, alpha, peak, negative, inductance, tons = decode(q)
    result = event_ring(initial, negative, lphase=inductance, ton=tons)
    if not result.passed:return None,result,None
    period=result.history[-1]["next_high_on_ns"]
    spacing=np.array([h["phase_spacing_ns"] for h in result.history])
    peaks=np.array([h["peak_a"] for h in result.history])
    module_current=float(result.charge_a_ns.sum()/period)
    residual=np.r_[result.final[1:]-initial[1:],spacing-SLOT*1e9,
                   peaks-peak,module_current-TARGET_MODULE_CURRENT_A]
    drift=result.final-initial
    fly_dv=np.array([drift[0]-drift[2],drift[1]-drift[3]])
    metrics=dict(period_ns=period,spacings_ns=spacing.tolist(),peaks_a=peaks.tolist(),
                 peak_target_a=peak,module_average_current_a=module_current,
                 state_return=drift.tolist(),fly_voltage_return_V=fly_dv.tolist(),
                 fly_charge_return_C=(CFLY*fly_dv).tolist())
    return residual,result,metrics


def norm(q):
    residual,_,_=raw(q)
    return np.full(len(SCALE),1e6) if residual is None else residual/SCALE


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    prior=json.loads((HERE/"numerical_runs/05_negative_valley_corrected/negative_corrected_refined.json").read_text())
    q0=np.r_[prior["initial_state"][1:],prior["negative_fraction"],
             prior["inductance_nH"],[prior["ton_ns"]]*3]
    lo=np.r_[[3,2.5,-.5,-.5,-10,5,20],.05,15.,[450.]*3]
    hi=np.r_[[5,5.5,.5,.5,20,55,90],.10,50.,[620.]*3]
    print("initial max violation",np.max(abs(norm(q0))),flush=True)
    fit=least_squares(norm,q0,bounds=(lo,hi),x_scale="jac",diff_step=1e-5,
                      ftol=1e-12,xtol=1e-12,gtol=1e-12,max_nfev=220,verbose=2)
    residual,result,metrics=raw(fit.x); normalized=residual/SCALE
    initial,alpha,peak,negative,inductance,tons=decode(fit.x)
    checks={
        "event_ring":bool(result.passed),
        "voltage_return":bool(np.max(abs(residual[:4]))<=V_RETURN_TOL),
        "current_return":bool(np.max(abs(residual[4:7]))<=I_RETURN_TOL),
        "equal_spacing":bool(np.max(abs(residual[7:10]))<=SPACING_TOL_NS),
        "corrected_peak_current":bool(np.max(abs(residual[10:13]))<=PEAK_TOL_A),
        "module_power":bool(abs(residual[13])<=MODULE_CURRENT_TOL_A),
        "negative_fraction_range":bool(.05<=alpha<=.10),
    }
    payload={
        "branch_status":"control sensitivity; per-phase Ton is not P25 explicit",
        "optimizer_success_flag":bool(fit.success),"message":fit.message,
        "nfev":int(fit.nfev),"cost":float(fit.cost),
        "negative_fraction":float(alpha),"negative_target_a":float(negative),
        "corrected_peak_target_a":float(peak),"inductance_nH":inductance*1e9,
        "ton_by_phase_ns":(tons*1e9).tolist(),"initial_state":initial.tolist(),
        "metrics":metrics,"raw_residual":residual.tolist(),
        "normalized_residual":normalized.tolist(),
        "max_acceptance_violation_factor":float(np.max(abs(normalized))),
        "checks":checks,"strict_pass":bool(all(checks.values())),
        "claim_limit":"single local start; per-phase timing is a diagnostic freedom",
    }
    (OUT/"per_phase_ton_fit.json").write_text(json.dumps(payload,indent=2))
    print(json.dumps(payload,indent=2))


if __name__=="__main__":main()
