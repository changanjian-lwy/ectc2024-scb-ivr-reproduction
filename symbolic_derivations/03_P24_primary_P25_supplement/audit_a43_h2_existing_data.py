"""Audit saved A43 data against an ideal Schur model; never runs SPICE."""
import json
from pathlib import Path
import numpy as np
from spicelib import RawRead

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CASE = ROOT/'experiments/track_A_periodic_steady_state/A43_p25_device_augmented_7p77_full_event_machine'

def main():
    raw = RawRead(str(CASE/'A43_p25_device_augmented_7p77_full_event_machine.raw'))
    def w(name):
        return np.real(raw.get_trace(name).get_wave(0))
    time = w('time')
    gate = w('V(xmod:gl2)')
    edge = int(np.flatnonzero((gate[:-1]>=2.5)&(gate[1:]<2.5))[0]+1)
    a = np.array([w(f'V(xmod:a{k})') for k in range(1,4)])
    x = np.array([w(f'V(xmod:x{k})') for k in range(1,5)])
    current = w('I(xmod:LIND2)')
    vh = a[0]-a[1]
    minimum = edge+int(np.argmin(vh[edge:]))
    # Exact A43 parameter provenance: saved netlist + GS library.
    ch, cl, fly, inductance, vo = 385e-12, 770e-12, 53.8e-6, 1.466666666666667e-9, 1.
    A=np.array([[fly+2*ch,-ch,0],[-ch,fly+2*ch,-ch],[0,-ch,fly+2*ch]])
    b=np.array([0,fly,0])
    p=np.linalg.solve(A,b)
    ceq=fly+cl-b@p
    gamma=p[1]-p[0]
    # Physical start extracted from saved waveforms, not re-solved.
    x0, i0, vh0=float(x[1,edge]),float(current[edge]),float(vh[edge])
    xz=x0+vh0/gamma
    amplitude=np.hypot(x0-vo,-i0*np.sqrt(inductance/ceq))
    xmax=vo+amplitude
    predicted_min=vh0-gamma*(xmax-x0)
    required=np.sqrt(max(0.,ceq/inductance*((xz-vo)**2-(x0-vo)**2)))
    omega=1/np.sqrt(inductance*ceq)
    peak_delay=np.arctan2(-i0*np.sqrt(inductance/ceq),x0-vo)/omega
    # Compare only the first rising swing, ending at saved minimum.
    idx=np.arange(edge,minimum+1)
    tau=time[idx]-time[edge]
    predicted_x=vo+(x0-vo)*np.cos(omega*tau)-i0*np.sqrt(inductance/ceq)*np.sin(omega*tau)
    predicted_v=vh0-gamma*(predicted_x-x0)
    result={
        'scope':'existing A43 waveform audit; ideal inactive-node clamp; no SPICE run or retuning',
        'release_time_ns':float(time[edge]*1e9),'release_current_a':i0,
        'release_x2_v':x0,'release_high_vds_v':vh0,
        'release_other_x_v':x[[0,2,3],edge].tolist(),
        'release_a_v':a[:,edge].tolist(),
        'full_module_ceq_pf':float(ceq*1e12),'gamma_h2':float(gamma),
        'isolated_cell_ceq_pf':float((cl+ch*fly/(ch+fly))*1e12),
        'predicted_vds_min_v':float(predicted_min),
        'saved_vds_min_v':float(vh[minimum]),
        'predicted_peak_delay_ns':float(peak_delay*1e9),
        'saved_peak_delay_ns':float((time[minimum]-time[edge])*1e9),
        'first_swing_vds_rmse_v':float(np.sqrt(np.mean((predicted_v-vh[idx])**2))),
        'ideal_required_release_current_a':float(required),
        'ideal_required_fraction_of_125a_pct':float(required/125*100),
        'limitations':['A43 includes finite Ron and reverse clamps; ideal reduction does not',
                      'required current holds the extracted release state fixed; not a controller sweep',
                      'no four-phase periodic closure or hardware threshold claim']}
    (HERE/'A43_H2_ANALYTICAL_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
