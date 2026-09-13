"""Aggregate audit of the P24 target branch and P25 evidence branches."""

from __future__ import annotations

from r04d0_regression import validate_existing_result as d0
from r04d0e_regression import validate_existing_result as d0e
from r04d1b2_regression import validate_existing_result as d1b2
from r04d2_regression import validate_existing_results as d2
from r04d3_regression import validate_existing_results as d3
from r04d3c_regression import validate_existing_result as d3c
from r04d3d_regression import validate_existing_result as d3d
from r04d3e_regression import validate_existing_result as d3e
from r04d4a_regression import validate_existing_result as d4
from r04d5a_regression import validate_existing_result as d5
from r04d6a_regression import validate_existing_result as d6


def revalidate() -> dict:
    raw = {
        "P24_R04D0_first_interval": d0(),
        "P25_to_NP4_R04D0E_first_interval": d0e(),
        "shared_R04D1B2_device_commutation": d1b2(),
        "separate_R04D2_interval2": d2(),
        "separate_R04D3_failures": d3(),
        "cross_paper_R04D3C_5pct_failure": d3c(),
        "model_R04D3D_threshold": d3d(),
        "model_R04D3E_8pct_exit": d3e(),
        "P25_native_R04D4_mode4": d4(),
        "P25_native_R04D5_mode5": d5(),
        "P25_native_R04D6_mode6": d6(),
    }
    regressions_pass = all(item["passed"] for item in raw.values())
    conclusions = {
        "p24_source_native_complete": False,
        "p24_reason": "P24 1%-2% does not reach high-side ZVS with the selected GS61008T scalar-capacitance plug-in.",
        "p24_model_calibrated_local_chain": raw["model_R04D3E_8pct_exit"]["passed"],
        "p25_to_np4_continuous_chain": False,
        "p25_to_np4_reason": "Mode-3 entrance has iL2<0 and moves away from the required zero crossing.",
        "p25_native_modes4_to6_continuous_from_mode3": False,
        "p25_native_reason": "Mode 4 starts from a controlled local iL2=0 boundary, not from the failed prior nP=4/48-V branch.",
        "p25_native_mode4_local": raw["P25_native_R04D4_mode4"]["passed"],
        "p25_native_mode5_local": raw["P25_native_R04D5_mode5"]["passed"],
        "p25_native_mode6_qualitative": raw["P25_native_R04D6_mode6"]["passed"],
        "p25_native_mode6_quantitative": False,
        "mode6_reason": "Physical circuit, printed Eq. (15)/(16), and 2Io/(nP*nM) peak values do not close.",
    }
    return {"regressions_pass": regressions_pass, "results": raw, "conclusions": conclusions}


if __name__ == "__main__":
    result = revalidate()
    print(result["conclusions"])
    if not result["regressions_pass"]:
        raise SystemExit("two-branch regression audit failed")
