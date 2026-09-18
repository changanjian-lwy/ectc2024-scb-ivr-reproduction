"""Parser for LTspice batch `.meas` output, shared by A52's pilot and main run.

LTspice prints two shapes, and they must NOT be parsed with one regex -- a
naive "first number after an `=`" rule silently reads the `0` out of
`V(vds)=0` and reports every zero-crossing as happening at t=0.  That bug
occurred in this experiment's own first pilot iteration and is the reason
this parser exists as a separate, explicitly-tested module.

  WHEN form:  `t_gh_on: V(gh)={VTH}  AT 2.00090542241e-09`
              -> the RESULT is the number after the trailing ` AT `.

  FIND form:  `vds_at_on: V(vds) =-0.00905887469819 at 2.00090542241e-09`
              -> the RESULT is the number after `=`; the number after the
                 trailing lowercase ` at ` is the time it was sampled at.

  PARAM form: `dvc1: dvc1=1.234e-03`
              -> the RESULT is the number after the last `=`.

  RANGE form: `vout_avg: AVG(V(out) )=0.687945 FROM 0 TO 2e-07`
              `imax_p1: MAX(ABS(I(LIND1)) )=100.3008 FROM 0 TO 2.5e-07`
              -> the RESULT is the number between `)=` and ` FROM `.  This
                 covers AVG/MIN/MAX/RMS/PP/INTEG.  Note the trailing
                 ` FROM ... TO ...`: without a dedicated pattern these
                 lines match nothing and every AVG/MIN/MAX silently reads
                 back as `None`.

A measurement whose condition never occurs prints a FAIL line and is
recorded as `None`, which is exactly the "this event never happened"
signal a ZVS verdict needs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_WHEN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*.*?\sAT\s+(-?[0-9.]+(?:e[+-]?\d+)?)\s*$")
_FIND = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*):\s*.*?=\s*(-?[0-9.]+(?:e[+-]?\d+)?)"
    r"\s+at\s+(-?[0-9.]+(?:e[+-]?\d+)?)\s*$"
)
_PARAM = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*):\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*"
    r"(-?[0-9.]+(?:e[+-]?\d+)?)\s*$"
)
_RANGE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*):\s*[A-Za-z_]+\(.*\)\s*=\s*"
    r"(-?[0-9.]+(?:e[+-]?\d+)?)\s+FROM\s+",
    re.I,
)
_FAIL = re.compile(r"^Measurement\s+\"?([A-Za-z_][A-Za-z0-9_]*)\"?\s+FAIL", re.I)


@dataclass(frozen=True)
class MeasResult:
    values: dict[str, float | None]
    #: For FIND-form measurements, the time the value was sampled at.
    times: dict[str, float]
    netlist_error: bool
    text: str

    def get(self, name: str) -> float | None:
        return self.values.get(name.lower())


def parse(log_path: Path) -> MeasResult:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    values: dict[str, float | None] = {}
    times: dict[str, float] = {}
    for raw in text.splitlines():
        line = raw.strip()
        fail = _FAIL.match(line)
        if fail:
            values.setdefault(fail.group(1).lower(), None)
            continue
        # RANGE must be tried BEFORE the others: `MIN(V(x))=0 FROM 0 TO 2.5e-07`
        # would otherwise be swallowed by a looser pattern.
        range_form = _RANGE.match(line)
        if range_form:
            values[range_form.group(1).lower()] = float(range_form.group(2))
            continue
        when = _WHEN.match(line)
        if when:
            values[when.group(1).lower()] = float(when.group(2))
            continue
        find = _FIND.match(line)
        if find:
            values[find.group(1).lower()] = float(find.group(2))
            times[find.group(1).lower()] = float(find.group(3))
            continue
        param = _PARAM.match(line)
        if param:
            values[param.group(1).lower()] = float(param.group(2))
    netlist_error = (
        "Expected device instantiation" in text
        or "Expected a sequence" in text
        or "Fatal Error" in text
        or "Voltage not found" in text
    )
    return MeasResult(values, times, netlist_error, text)


def _selftest() -> None:
    """Guard the exact shapes that broke the first iteration's parser."""
    import tempfile

    sample = (
        "t_dt_enter: V(pstate)=0.5  AT 1.00071388769e-09\n"
        "t_gh_on: V(gh)={VTH}  AT 2.00090542241e-09\n"
        "vds_at_on: V(vds) =-0.00905887469819 at 2.00090542241e-09\n"
        "t_vds_cross: V(vds)=0  AT 1.9999994985e-09\n"
        "vds_before_wend: V(vds) =-0.070000000298 at 3.149999e-09\n"
        "dvc1: dvc1=1.5e-03\n"
        "vout_avg: AVG(V(out) )=0.687945333889 FROM 0 TO 2e-07\n"
        "vsrc_min: MIN(V(src))=0 FROM 0 TO 2.5e-07\n"
        "imax_p1: MAX(ABS(I(LIND1)) )=100.300872803 FROM 0 TO 2.5e-07\n"
        "vdsmin_p1: MIN(V(vin,a1) )=-0.0870056152344 FROM 1.9785e-07 TO 2e-07\n"
        'Measurement "t_missing" FAIL\'ed\n'
    )
    with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as handle:
        handle.write(sample)
        path = Path(handle.name)
    result = parse(path)
    assert result.get("t_vds_cross") == 1.9999994985e-09, result.get("t_vds_cross")
    assert result.get("t_dt_enter") == 1.00071388769e-09
    assert result.get("t_gh_on") == 2.00090542241e-09
    assert result.get("vds_at_on") == -0.00905887469819
    assert result.times["vds_at_on"] == 2.00090542241e-09
    assert result.get("vds_before_wend") == -0.070000000298
    assert result.get("dvc1") == 1.5e-03
    assert result.get("vout_avg") == 0.687945333889, result.get("vout_avg")
    assert result.get("vsrc_min") == 0.0
    assert result.get("imax_p1") == 100.300872803
    assert result.get("vdsmin_p1") == -0.0870056152344
    assert "t_missing" in result.values and result.get("t_missing") is None
    assert not result.netlist_error
    path.unlink()
    print("meas_log selftest OK")


if __name__ == "__main__":
    _selftest()
