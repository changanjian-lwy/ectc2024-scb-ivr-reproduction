"""Add explicit flying-capacitor charge-return equations to the sensitivity fit."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from strict_joint_per_phase_ton import HERE, OUT, raw, decode
from strict_joint_p25_fit import (
    SCALE, V_RETURN_TOL, I_RETURN_TOL, SPACING_TOL_NS, PEAK_TOL_A,
    MODULE_CURRENT_TOL_A,
)


def extended_raw(q):
    base, result, metrics = raw(q)
    if base is None:return None,result,metrics
    fly=np.asarray(metrics["fly_voltage_return_V"])
    return np.r_[base,fly],result,metrics


def main():
    src=json.loads((OUT/"per_phase_ton_fit.json").read_text())
    q0=np.r_[src["initial_state"][1:],src["negative_fraction"],
             src["inductance_nH"],src["ton_by_phase_ns"]]
    # Original 14 acceptance scales plus two explicit flying-voltage returns.
    scale=np.r_[SCALE,[V_RETURN_TOL,V_RETURN_TOL]]
    search=scale.copy(); search[10:13]*=.75; search[14:]*=.5
    def objective(q):
        residual,_,_=extended_raw(q)
        return np.full(len(scale),1e6) if residual is None else residual/search
    lo=np.r_[[3,2.5,-.5,-.5,-10,5,20],.05,15.,[450.]*3]
    hi=np.r_[[5,5.5,.5,.5,20,55,90],.10,50.,[620.]*3]
    fit=least_squares(objective,q0,bounds=(lo,hi),x_scale="jac",diff_step=1e-5,
                      ftol=1e-12,xtol=1e-12,gtol=1e-12,max_nfev=220,verbose=2)
    residual,result,metrics=extended_raw(fit.x); accept=residual/scale
    initial,alpha,peak,negative,inductance,tons=decode(fit.x)
    checks={
        "event_ring":bool(result.passed),
        "voltage_return":bool(np.max(abs(residual[:4]))<=V_RETURN_TOL),
        "current_return":bool(np.max(abs(residual[4:7]))<=I_RETURN_TOL),
        "equal_spacing":bool(np.max(abs(residual[7:10]))<=SPACING_TOL_NS),
        "corrected_peak_current":bool(np.max(abs(residual[10:13]))<=PEAK_TOL_A),
        "module_power":bool(abs(residual[13])<=MODULE_CURRENT_TOL_A),
        "flying_charge_return":bool(np.max(abs(residual[14:16]))<=V_RETURN_TOL),
        "negative_fraction_range":bool(.05<=alpha<=.10),
    }
    payload={
        "branch_status":"control sensitivity; per-phase Ton is not P25 explicit",
        "explicit_flying_charge_balance":True,
        "optimizer_success_flag":bool(fit.success),"message":fit.message,
        "nfev":int(fit.nfev),"cost_in_search_metric":float(fit.cost),
        "negative_fraction":float(alpha),"negative_target_a":float(negative),
        "corrected_peak_target_a":float(peak),"inductance_nH":inductance*1e9,
        "ton_by_phase_ns":(tons*1e9).tolist(),"initial_state":initial.tolist(),
        "metrics":metrics,"extended_raw_residual":residual.tolist(),
        "acceptance_normalized_residual":accept.tolist(),
        "max_acceptance_violation_factor":float(np.max(abs(accept))),
        "checks":checks,"strict_pass":bool(all(checks.values())),
        "claim_limit":"single local refinement; extra per-phase timing is diagnostic only",
    }
    (OUT/"per_phase_ton_charge_refined.json").write_text(json.dumps(payload,indent=2))
    print(json.dumps(payload,indent=2))


if __name__=="__main__":main()
