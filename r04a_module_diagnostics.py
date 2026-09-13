"""Map R04A measurements back to the module responsible for each claim."""

from __future__ import annotations

import json
from pathlib import Path

from assembly_planner import assemble
from experiment_profiles import R04A_LOCAL_BOUNDARY_REPLAY
from module_diagnostics import CheckResult, CheckStatus, structural_diagnostics, summarize
from r04a_regression import validate_existing_result


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "outputs/diagnostics/R04A_module_diagnostics.json"


def diagnose() -> dict:
    plan = assemble(R04A_LOCAL_BOUNDARY_REPLAY)
    regression = validate_existing_result()
    peaks = regression["measurements"]["i_max_a"]
    ton = regression["measurements"]["ton_s"]

    checks = list(structural_diagnostics(plan))
    checks.extend(
        (
            CheckResult(
                "R04A:p24_on_time",
                "p24_equations_1_to_6",
                CheckStatus.PASS
                if all(abs(x - 16.6666666667e-9) <= 1e-13 for x in ton)
                else CheckStatus.FAIL,
                f"{[x * 1e9 for x in ton]} ns",
                "both branches use P24 Eq.(3) Ton = 16.6667 ns",
                "validates equation transfer into this local netlist only",
            ),
            CheckResult(
                "R04A:eq4_peak",
                "p24_derived_single_phase_stiff_boundary",
                CheckStatus.PASS if abs(peaks[0] - 125.0) <= 0.25 else CheckStatus.FAIL,
                f"{peaks[0]:.6f} A",
                "125 A +/- 0.25 A",
                "stiff Vin/nP-to-Vo analytical boundary; not the full FC network",
            ),
            CheckResult(
                "R04A:table_branch_separation",
                "p24_equations_1_to_6",
                CheckStatus.PASS if abs(peaks[1] - 68.5) <= 0.25 else CheckStatus.FAIL,
                f"{peaks[1]:.6f} A",
                "about 68.5 A for the independent Table-I 2.68-nH audit branch",
                "preserves the printed Eq.(4)/Table-I conflict; does not resolve it",
            ),
            CheckResult(
                "R04A:state_progression",
                "ltspice_latched_event_memory",
                CheckStatus.PASS if regression["passed"] else CheckStatus.FAIL,
                "HS -> LS positive -> zero crossing -> small-negative state",
                "latched progression without comparator chatter",
                "numerical state memory only; no physical controller delay claim",
            ),
            CheckResult(
                "R04A:coss_zvs",
                "ideal_switch_pair",
                CheckStatus.NOT_APPLICABLE,
                "Coss/dead-time stage absent",
                "not evaluated in R04A",
                "the ideal-switch module cannot establish hardware ZVS or loss",
            ),
        )
    )
    checks_tuple = tuple(checks)
    return {
        "experiment_id": R04A_LOCAL_BOUNDARY_REPLAY.experiment_id,
        "assembly_ready": plan.ready,
        "selected_modules": [m.module_id for m in plan.selected_modules],
        "module_checks": [check.as_dict() for check in checks_tuple],
        "summary": summarize(checks_tuple),
        "final_claim": regression["claim_boundary"],
    }


def main() -> None:
    result = diagnose()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["summary"]["passed"]:
        raise SystemExit("R04A module diagnostic failed")


if __name__ == "__main__":
    main()
