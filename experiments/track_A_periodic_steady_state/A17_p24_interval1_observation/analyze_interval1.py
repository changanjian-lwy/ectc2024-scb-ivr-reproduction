"""Extract P24 Interval 1 from the unchanged A16 LTspice result."""

from pathlib import Path

import numpy as np
from spicelib import RawRead


HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "A16_tighten_04_C3" / "A16_tighten_only_C3_from_A15.raw"

VIN = 48.0
VO = 1.0
FSW = 5e6
NP = 4
L = 1.466666666666667e-9
IPEAK = 125.0
TON = NP * VO / VIN / FSW


def sample(time: np.ndarray, wave: np.ndarray, instant: float) -> tuple[float, float]:
    index = int(np.argmin(np.abs(time - instant)))
    return float(time[index]), float(wave[index])


raw = RawRead(str(RAW))
time = np.real(raw.get_trace("time").get_wave(0))
i_l1 = np.real(raw.get_trace("I(xmod:L1)").get_wave(0))
v_x1 = np.real(raw.get_trace("V(xmod:x1)").get_wave(0))
v_out = np.real(raw.get_trace("V(out)").get_wave(0))

# Avoid the exact discontinuity at t=0; A16 measurements use the same 2 ps rule.
t_start, i_start = sample(time, i_l1, 2e-12)
t_end, i_end = sample(time, i_l1, TON + 2e-12)
_, vx_start = sample(time, v_x1, 2e-12)
_, vx_end = sample(time, v_x1, TON + 2e-12)
_, vo_start = sample(time, v_out, 2e-12)
_, vo_end = sample(time, v_out, TON + 2e-12)

mask = (time >= t_start) & (time <= t_end)
delta_i = i_end - i_start
measured_slope = delta_i / (t_end - t_start)
effective_v_from_slope = L * measured_slope

print(f"source_raw={RAW}")
print(f"ton_ns={TON * 1e9:.9f}")
print(f"sample_start_ns={t_start * 1e9:.9f}")
print(f"sample_end_ns={t_end * 1e9:.9f}")
print(f"il1_start_A={i_start:.9f}")
print(f"il1_end_A={i_end:.9f}")
print(f"delta_il1_A={delta_i:.9f}")
print(f"il1_min_interval_A={float(np.min(i_l1[mask])):.9f}")
print(f"il1_max_interval_A={float(np.max(i_l1[mask])):.9f}")
print(f"measured_didt_A_per_ns={measured_slope / 1e9:.9f}")
print(f"effective_vL_from_slope_V={effective_v_from_slope:.9f}")
print(f"x1_start_V={vx_start:.9f}")
print(f"x1_end_V={vx_end:.9f}")
print(f"vo_start_V={vo_start:.9f}")
print(f"vo_end_V={vo_end:.9f}")
print(f"peak_target_A={IPEAK:.9f}")
print(f"end_minus_peak_target_A={i_end - IPEAK:.9f}")
print(f"end_over_peak_target_pct={100.0 * i_end / IPEAK:.6f}")
print(f"pass_current_rises={i_end > i_start}")
