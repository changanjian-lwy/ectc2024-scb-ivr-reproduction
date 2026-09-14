"""Observe P24 Interval-2 phase-1 current decay in the unchanged A16 orbit."""

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


raw = RawRead(str(RAW))
time = np.real(raw.get_trace("time").get_wave(0))
i_l1 = np.real(raw.get_trace("I(xmod:L1)").get_wave(0))
v_x1 = np.real(raw.get_trace("V(xmod:x1)").get_wave(0))

commutation = np.where((time > T1) & (v_x1 <= 0.0))[0]
if len(commutation) == 0:
    raise SystemExit("FAIL: no QL1 zero-voltage opportunity after t1")
i_comm = int(commutation[0])

crossings = np.where((np.arange(len(time)) > i_comm) & (i_l1 <= 0.0))[0]
if len(crossings) == 0:
    raise SystemExit("FAIL: iL1 did not reach zero after the commutation event")
i_zero = int(crossings[0])

segment = i_l1[i_comm : i_zero + 1]
print(f"source_raw={RAW}")
print(f"low_side_zvs_opportunity_ns={time[i_comm] * 1e9:.9f}")
print(f"il1_at_zvs_opportunity_A={i_l1[i_comm]:.9f}")
print(f"first_il1_zero_ns={time[i_zero] * 1e9:.9f}")
print(f"il1_at_zero_sample_A={i_l1[i_zero]:.9f}")
print(f"decay_duration_ns={(time[i_zero] - time[i_comm]) * 1e9:.9f}")
print(f"vds_ql1_before_zero_A18_V={v_x1[i_comm]:.9f}")
print(f"vds_ql1_at_il1_zero_V={v_x1[i_zero]:.9f}")
print(f"segment_start_minus_end_A={segment[0] - segment[-1]:.9f}")
print(f"pass_reaches_zero={i_l1[i_zero] <= 0.0}")
print(f"pass_net_current_decrease={segment[-1] < segment[0]}")
