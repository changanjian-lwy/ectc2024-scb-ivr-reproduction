"""Position comparison and saved A37/A43 event audit; no SPICE invocation."""
import json
from pathlib import Path
import numpy as np
from spicelib import RawRead

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TRACK=ROOT/'experiments/track_A_periodic_steady_state'
CH,CL,FLY,L,VO=385e-12,770e-12,53.8e-6,1.466666666666667e-9,1.
A=np.array([[FLY+2*CH,-CH,0],[-CH,FLY+2*CH,-CH],[0,-CH,FLY+2*CH]])
BF=np.array([[FLY,0,0,0],[0,FLY,0,0],[0,0,FLY,CH]])
D=np.array([FLY+CL]*3+[CH+CL])
DS=np.array([[-1,0,0],[1,-1,0],[0,1,-1],[0,0,1]])

def geometry(s):
    p=np.linalg.solve(A,BF[:,s])
    return D[s]-BF[:,s]@p,float(s==3)-DS[s]@p

def first_cross(t,v,level,direction):
    mask=(v[:-1]>level)&(v[1:]<=level) if direction<0 else (v[:-1]<level)&(v[1:]>=level)
    ids=np.flatnonzero(mask)
    if not len(ids): return None
    k=int(ids[0])
    return float(t[k]+(level-v[k])/(v[k+1]-v[k])*(t[k+1]-t[k]))

def audit(label,path):
    raw=RawRead(str(path))
    def w(n): return np.real(raw.get_trace(n).get_wave(0))
    t=w('time')
    a=np.array([w(f'V(xmod:a{k})') for k in range(1,4)])
    x=np.array([w(f'V(xmod:x{k})') for k in range(1,5)])
    vh=np.array([w('V(vin)')-a[0],a[0]-a[1],a[1]-a[2],a[2]-x[3]])
    out=[]
    for s in range(4):
        low=w(f'V(xmod:gl{s+1})')
        high=w(f'V(xmod:gh{s+1})')
        edges=np.flatnonzero((low[:-1]>=2.5)&(low[1:]<2.5))+1
        if not len(edges):
            out.append({'phase':s+1,'release_observed':False,'status':'not reached; no invented release state'})
            continue
        k=int(edges[0]); ceq,gamma=geometry(s)
        i0=float(w(f'I(xmod:LIND{s+1})')[k]); x0=float(x[s,k]); v0=float(vh[s,k])
        target=x0+v0/gamma-VO
        av=x0-VO; bv=-i0*np.sqrt(L/ceq); radius=np.hypot(av,bv)
        can=bool(gamma>0 and target>0 and radius>=target and i0<0)
        zdelay=None
        if can:
            phi=np.arctan2(bv,av); ang=np.arccos(target/radius)
            roots=[(phi-ang)%(2*np.pi),(phi+ang)%(2*np.pi)]
            zdelay=float(min(z for z in roots if z>0)*np.sqrt(L*ceq))
        # Limited to this first swing; not later oscillations or changed topology.
        ids=np.arange(k,len(t)); ids=ids[t[ids]<=t[k]+10e-9]
        zsaved=first_cross(t[ids],vh[s,ids],0,-1)
        admitted=first_cross(t[ids],high[ids],2.5,1)
        if admitted is not None: ids=ids[t[ids]<=admitted]
        required=float(np.sqrt(max(0.,ceq/L*(target**2-av**2))))
        out.append({'phase':s+1,'release_observed':True,'release_time_ns':float(t[k]*1e9),
                    'release_current_a':i0,'release_x_v':x0,'release_vds_v':v0,
                    'ceq_pf':float(ceq*1e12),'gamma':float(gamma),
                    'ideal_required_current_a':required,'ideal_required_pct':required/125*100,
                    'ideal_natural_zvs_reachable':can,
                    'unclamped_predicted_min_v':float(v0-gamma*(VO+radius-x0)),
                    'saved_min_in_first_10ns_before_admission_v':float(np.min(vh[s,ids])),
                    'predicted_first_zero_ns':None if zdelay is None else float((t[k]+zdelay)*1e9),
                    'saved_first_zero_ns':None if zsaved is None else zsaved*1e9,
                    'saved_high_admission_ns':None if admitted is None else admitted*1e9})
    return {'case':label,'raw_path':str(path.relative_to(ROOT)),'events':out}

def main():
    results={'scope':'fixed old device library; geometry calculation and saved data audit only',
             'position_geometry':[{'phase':s+1,'ceq_pf':float(geometry(s)[0]*1e12),'gamma':float(geometry(s)[1])} for s in range(4)],
             'cases':[audit('A43 7.77%',TRACK/'A43_p25_device_augmented_7p77_full_event_machine/A43_p25_device_augmented_7p77_full_event_machine.raw'),
                      audit('A37 9% iteration 001 selected seed',TRACK/'A37_solver_work/iter_001.raw')],
             'limitations':['geometry values use old GS fixture, not a new experiment',
                            'only phases with recorded release events are compared',
                            'ideal inactive-node clamp differs from finite-Ron saved cases',
                            'negative unclamped minimum means a clamp/mode change occurs, not a valid later trajectory',
                            'required percentages freeze each extracted state, not controller thresholds',
                            'no full periodic orbit or hardware conclusion']}
    (HERE/'FOUR_POSITIONS_EXISTING_CASES_AUDIT.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
