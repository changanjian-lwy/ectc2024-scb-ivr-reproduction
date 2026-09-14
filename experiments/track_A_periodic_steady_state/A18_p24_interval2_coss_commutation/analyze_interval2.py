"""Extract the P24 t1 Coss commutation from the unchanged A16 raw result."""

from pathlib import Path

import numpy as np
from spicelib import RawRead


HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "A16_tighten_04_C3" / "A16_tighten_only_C3_from_A15.raw"

VIN = 48.0
VO = 1.0
FSW = 5e6
NP = 4
T1 = NP * VO / VIN / FSW


def nearest(time: np.ndarray, instant: float) -> int:
    return int(np.argmin(np.abs(time - instant)))


raw = RawRead(str(RAW))
time = np.real(raw.get_trace("time").get_wave(0))
i_l1 = np.real(raw.get_trace("I(xmod:L1)").get_wave(0))
v_x1 = np.real(raw.get_trace("V(xmod:x1)").get_wave(0))
v_a1 = np.real(raw.get_trace("V(xmod:a1)").get_wave(0))
vds_h1 = VIN - v_a1

# Sample 1 ps after the ideal high-side edge; search only the following 2 ns.
i_start = nearest(time, T1 + 1e-12)
window = np.where((time > T1) & (time <= T1 + 2e-9))[0]
zero_candidates = window[v_x1[window] <= 0.0]

if len(zero_candidates) == 0:
    raise SystemExit("FAIL: Vds(QL1) did not reach zero within 2 ns after t1")

i_zero = int(zero_candidates[0])
duration = time[i_zero] - T1

print(f"source_raw={RAW}")
print(f"t1_ns={T1 * 1e9:.9f}")
print(f"zero_time_ns={time[i_zero] * 1e9:.9f}")
print(f"commutation_duration_ns={duration * 1e9:.9f}")
print(f"vds_ql1_start_V={v_x1[i_start]:.9f}")
print(f"vds_ql1_at_zero_event_V={v_x1[i_zero]:.9f}")
print(f"vds_qh1_start_V={vds_h1[i_start]:.9f}")
print(f"vds_qh1_at_zero_event_V={vds_h1[i_zero]:.9f}")
print(f"il1_start_A={i_l1[i_start]:.9f}")
print(f"il1_at_zero_event_A={i_l1[i_zero]:.9f}")
print(f"pass_ql1_vds_reaches_zero={v_x1[i_zero] <= 0.0}")
print(f"pass_qh1_vds_rises={vds_h1[i_zero] > vds_h1[i_start]}")
print(f"pass_il1_remains_positive={i_l1[i_zero] > 0.0}")
