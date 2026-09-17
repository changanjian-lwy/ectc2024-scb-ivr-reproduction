"""Validate the P25-native local Mode-4 replay."""

from __future__ import annotations

import re
from validation.paths import PROJECT_ROOT


LOG = PROJECT_ROOT / "paper_locked/03_apec2025_auxiliary/spice/R04D4A_P25_native_mode4_local_5pct.log"


def _value(text: str, name: str, *, at: bool = False) -> float:
    line = re.search(rf"^{re.escape(name)}:(.*)$", text, re.MULTILINE)
    if not line:
        raise ValueError(f"measurement {name} absent")
    if at:
        match = re.search(r"\bAT\s+([-+0-9.eE]+)", line.group(1))
        if match:
            return float(match.group(1))
    vals = re.findall(r"=\s*([-+0-9.eE]+)", line.group(1))
    if not vals:
        raise ValueError(name)
    return float(vals[-1])


def validate_existing_result() -> dict:
    text = LOG.read_text(errors="replace")
    values = {
        "t4_s": _value(text, "t4_sl2_off", at=True),
        "il2_t4_a": _value(text, "il2_at_t4"),
        "ipeak_a": _value(text, "ipeak_derived"),
        "target_a": _value(text, "negative_target"),
        "fraction": _value(text, "negative_fraction"),
        "np": _value(text, "np_explicit"),
        "nm": _value(text, "nm_explicit"),
    }
    checks = {
        "p25_design_fraction": abs(values["fraction"] - 0.05) <= 1e-12,
        "architecture_explicit": values["np"] == 3 and values["nm"] == 3,
        "peak_from_paper_operating_point": abs(values["ipeak_a"] - 44.4444444444) < 1e-8,
        "negative_target_reached": abs(values["il2_t4_a"] + values["target_a"]) < 1e-3,
        "positive_duration": values["t4_s"] > 0,
    }
    return {"measurements": values, "checks": checks, "passed": all(checks.values()),
            "claim_boundary": "local P25 Mode 4 only; other-phase positive magnitudes and prior periodic state remain unresolved"}


if __name__ == "__main__":
    result = validate_existing_result()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04D4A failed")
