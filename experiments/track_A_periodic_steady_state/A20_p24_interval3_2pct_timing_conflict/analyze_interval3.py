"""Audit P24 Interval 3 without relaxing the cross-phase conduction rule."""

from pathlib import Path

import numpy as np
from spicelib import RawRead


HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "A16_tighten_04_C3" / "A16_tighten_only_C3_from_A15.raw"

VIN = 48.0
VO = 1.0
FSW = 5e6
NP = 4
IPEAK = 125.0
NEG_FRAC = 0.02
INEG = NEG_FRAC * IPEAK
T = 1.0 / FSW
TON = NP * VO / VIN / FSW
QH4_START = 3.0 * T / NP
QH4_END = QH4_START + TON
NEXT_QH1 = T


raw = RawRead(str(RAW))
time = np.real(raw.get_trace("time").get_wave(0))
i_l1 = np.real(raw.get_trace("I(xmod:L1)").get_wave(0))
v_a1 = np.real(raw.get_trace("V(xmod:a1)").get_wave(0))
v_x1 = np.real(raw.get_trace("V(xmod:x1)").get_wave(0))
vds_qh1 = VIN - v_a1


def nearest(instant: float) -> int:
    return int(np.argmin(np.abs(time - instant)))


zero = np.where((time > 100e-9) & (i_l1 <= 0.0))[0]
if len(zero) == 0:
    raise SystemExit("FAIL: no phase-1 zero crossing")
i_zero = int(zero[0])

threshold = np.where((np.arange(len(time)) > i_zero) & (i_l1 <= -INEG))[0]
if len(threshold) == 0:
    raise SystemExit("FAIL: no P24 2% negative-current event")
i_threshold = int(threshold[0])
i_release = nearest(QH4_END + 2e-12)

pre_next = np.where((time >= time[i_release]) & (time < NEXT_QH1))[0]
i_min_vds = int(pre_next[np.argmin(vds_qh1[pre_next])])
zvs_candidates = pre_next[vds_qh1[pre_next] <= 0.0]

print(f"source_raw={RAW}")
print(f"current_zero_ns={time[i_zero] * 1e9:.9f}")
print(f"p24_threshold_A={-INEG:.9f}")
print(f"threshold_event_ns={time[i_threshold] * 1e9:.9f}")
print(f"il1_at_threshold_A={i_l1[i_threshold]:.9f}")
print(f"qh4_support_end_ns={QH4_END * 1e9:.9f}")
print(f"threshold_precedes_support_end_ns={(QH4_END-time[i_threshold])*1e9:.9f}")
print(f"actual_release_sample_ns={time[i_release] * 1e9:.9f}")
print(f"il1_at_actual_release_A={i_l1[i_release]:.9f}")
print(f"actual_release_fraction_pct={-100*i_l1[i_release]/IPEAK:.9f}")
print(f"vds_qh1_at_release_V={vds_qh1[i_release]:.9f}")
print(f"minimum_vds_qh1_before_next_command_V={vds_qh1[i_min_vds]:.9f}")
print(f"minimum_vds_time_ns={time[i_min_vds]*1e9:.9f}")
print(f"il1_at_minimum_vds_A={i_l1[i_min_vds]:.9f}")
print(f"x1_at_minimum_vds_V={v_x1[i_min_vds]:.9f}")
print(f"pass_2pct_coincides_with_support_end={abs(time[i_threshold]-QH4_END)<=5e-12}")
print(f"pass_qh1_vds_reaches_zero_before_next_command={len(zvs_candidates)>0}")
