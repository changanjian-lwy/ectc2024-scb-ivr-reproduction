"""Lock the refined R04D3D transition between failure and ZVS."""

from __future__ import annotations

from pathlib import Path


LOG = Path(__file__).resolve().parent / "paper_locked/02_ectc2024_main/spice/R04D3D_negative_threshold_search_refined.log"


def validate_existing_result() -> dict:
    text = LOG.read_text(errors="replace")
    checks = {
        "refined_steps_present": ".step neg_frac=0.0776" in text and ".step neg_frac=0.0777" in text,
        "seven_point_76_fails": "     7\tfailed" in text,
        "seven_point_77_reaches_zero": "     8\t1.66468593861e-08" in text,
        "boundary_vds_values_present": "     7\t0.0139236450195" in text and "     8\t-4.95910644531e-05" in text,
        "boundary_current_values_present": "     7\t9.7" in text and "     8\t9.7125" in text,
    }
    return {
        "threshold_fraction": 0.0777,
        "threshold_current_a": -9.7125,
        "first_zero_crossing_s": 1.66468593861e-08,
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": "minimum observed threshold for the exact R04D3 numerical model only",
    }


if __name__ == "__main__":
    result = validate_existing_result()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04D3D threshold regression changed")
