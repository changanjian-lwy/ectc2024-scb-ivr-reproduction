"""Report the A26 guard decision without inferring an unreported delay policy."""

from pathlib import Path

import numpy as np
from spicelib import RawRead


HERE = Path(__file__).resolve().parent
raw = RawRead(str(HERE / "A26_h2_zvs_readiness_guard.raw"))
time = np.real(raw.get_trace("time").get_wave(0))


def w(name: str) -> np.ndarray:
    return np.real(raw.get_trace(name).get_wave(0))


a1 = w("V(xmod:a1)")
a2 = w("V(xmod:a2)")
vds = a1 - a2
gh2 = w("V(xmod:gh2)")
guard = w("V(xmod:h2_guard_state)")
start, end = 50e-9, 50e-9 + 16.6666666666667e-9
window = np.where((time >= start) & (time <= end))[0]
minimum = int(window[np.argmin(vds[window])])
request_sample = int(np.argmin(np.abs(time - start)))
end_sample = int(np.argmin(np.abs(time - end)))
gate_on = window[gh2[window] > 2.5]
zero = window[vds[window] <= 0.0]

print(f"vds_at_request_V={vds[request_sample]:.9f}")
print(f"minimum_vds_in_request_window_V={vds[minimum]:.9f}")
print(f"minimum_vds_time_ns={time[minimum]*1e9:.9f}")
print(f"guard_state_at_window_end={guard[end_sample]:.9f}")
print(f"sh2_ever_commanded_in_window={len(gate_on)>0}")
print(f"vds_reached_zero_in_window={len(zero)>0}")
print(f"pass_guard_prevented_hard_turnon={len(gate_on)==0 or len(zero)>0}")
print(f"pass_phase2_zvs_completed={len(gate_on)>0 and len(zero)>0}")
if len(zero):
    first_zero = int(zero[0])
    print(f"first_vds_zero_ns={time[first_zero]*1e9:.9f}")
    print(f"wait_from_nominal_request_ns={(time[first_zero]-start)*1e9:.9f}")
if len(gate_on):
    first_gate = int(gate_on[0])
    print(f"first_sh2_gate_on_ns={time[first_gate]*1e9:.9f}")
    print(f"remaining_on_window_ns={(end-time[first_gate])*1e9:.9f}")
