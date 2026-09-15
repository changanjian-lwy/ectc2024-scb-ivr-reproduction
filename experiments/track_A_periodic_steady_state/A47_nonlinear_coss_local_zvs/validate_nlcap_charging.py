"""Standalone validation of the nonlinear Coss(V) LTspice capacitor model,
required by the task before wiring it into the real A47 commutation chain.

Builds a minimal two-node netlist (a constant current source charging the
same nonlinear capacitor construction used in A47 stage 1/2), runs it in
real LTspice, and compares the resulting V(t) against direct numerical
integration (scipy.integrate.solve_ivp) of dV/dt = I / Coss(V) using the
exact same fitted Coss(V) parameters.

Implementation note (see BOUNDARY.md "LTspice implementation note" for the
full story): LTspice's native `Cxxx n1 n2 Q=<expr>` nonlinear-capacitor
device was tried first for this exact Coss(V) shape and pathologically
collapsed its own internal timestep to ~1e-17 s regardless of tolerance
settings or an added floating-node-safety leak resistor -- for both the
atan-based Q(V) used here and an alternative power-law Q(V). The
numerically robust construction actually used everywhere in A47 is a
behavioral current source using LTspice's ddt() time-derivative operator,
`B<name> n1 n2 I=ddt(Q(V(n1,n2)))`, which is electrically identical to a
charge-controlled capacitor. This script validates exactly that construction
in isolation (a single B-source, no switches, no stiff LC/capacitor-loop
context) before A47 stage 1/2 embed it in the full commutation chain.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
RUNNER = PROJECT / "tools" / "ltspice_runner.sh"
NETLIST = HERE / "validate_nlcap_charging.cir"

CFLOOR_F = 203.754e-12
A_F = 498.502e-12
VKNEE = 13.1432
ITEST = 10.0
TSTOP = 5e-9
CHECK_TIMES_NS = (1.0, 2.0, 5.0)

NETLIST_TEXT = f"""\
* A47 standalone nonlinear-capacitor validation (see validate_nlcap_charging.py)
.param CFLOOR={CFLOOR_F} A={A_F} VKNEE={VKNEE}
.param ITEST={ITEST}

I1 0 n1 {{ITEST}}
B1 n1 0 I=ddt(CFLOOR*V(n1)+A*VKNEE*atan(V(n1)/VKNEE))
RLEAK n1 0 1G

.tran 0 {TSTOP} 0 1p UIC
.options reltol=1e-7 abstol=1e-10 chgtol=1e-16
.save V(n1)
.meas tran V_AT_1NS FIND V(n1) AT 1n
.meas tran V_AT_2NS FIND V(n1) AT 2n
.meas tran V_AT_5NS FIND V(n1) AT 5n
.end
"""


def coss(V: float) -> float:
    return CFLOOR_F + A_F / (1.0 + (V / VKNEE) ** 2)


def python_reference() -> dict[float, float]:
    def rhs(t, y):
        return [ITEST / coss(y[0])]

    sol = solve_ivp(rhs, [0, TSTOP], [0.0], max_step=1e-12, rtol=1e-10, atol=1e-14)
    out = {}
    for t_ns in CHECK_TIMES_NS:
        idx = int(np.argmin(np.abs(sol.t - t_ns * 1e-9)))
        out[t_ns] = float(sol.y[0][idx])
    return out


def run_ltspice() -> dict[float, float]:
    NETLIST.write_text(NETLIST_TEXT)
    subprocess.run([str(RUNNER), "run", str(NETLIST)], check=True)
    log = NETLIST.with_suffix(".log").read_text()
    out = {}
    for t_ns in CHECK_TIMES_NS:
        m = re.search(rf"v_at_{int(t_ns)}ns:\s*V\(n1\)\s*=\s*([0-9.eE+-]+)", log)
        if not m:
            raise RuntimeError(f"measurement for {t_ns}ns not found in {log}")
        out[t_ns] = float(m.group(1))
    return out


def main() -> None:
    py = python_reference()
    sp = run_ltspice()
    print(f"{'t (ns)':>8} {'python (V)':>14} {'ltspice (V)':>14} {'rel err %':>12}")
    max_rel = 0.0
    for t_ns in CHECK_TIMES_NS:
        rel = abs(sp[t_ns] - py[t_ns]) / py[t_ns] * 100.0
        max_rel = max(max_rel, rel)
        print(f"{t_ns:8.1f} {py[t_ns]:14.6f} {sp[t_ns]:14.6f} {rel:12.6f}")
    print(f"max relative error: {max_rel:.6f}%")
    if max_rel > 0.1:
        print("FAIL: LTspice nonlinear-capacitor construction does not match "
              "direct numerical integration within 0.1%", file=sys.stderr)
        sys.exit(1)
    print("PASS: LTspice B-source ddt(Q(V)) construction matches direct "
          "numerical integration of the same Coss(V).")


if __name__ == "__main__":
    main()
