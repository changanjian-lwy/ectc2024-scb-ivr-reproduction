"""Split each successful handoff into physical event intervals.

This is read-only post-processing. It never changes a gate event.
"""
import argparse,csv,json
from pathlib import Path
import numpy as np

def main():
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('--csv',type=Path);args=p.parse_args()
    events=[json.loads(x) for x in args.trace.read_text().splitlines()
            if x.startswith('{') and 'handoff' in json.loads(x)]
    rows=[];start=50.0
    for e in events:
        if 'failure' in e:break
        row=dict(handoff=e['handoff'],ring=e['handoff']//4+1,phase=e['active_phase'],
                 active_high_on_ns=start,
                 commanded_on_ns=e['high_off_ns']-start,
                 high_off_to_low_on_ns=e['low_on_ns']-e['high_off_ns'],
                 low_freewheel_to_target_ns=e['release_ns']-e['low_on_ns'],
                 release_to_next_high_zvs_ns=e['next_high_on_ns']-e['release_ns'],
                 full_handoff_ns=e['next_high_on_ns']-start,
                 next_entry_a=e['next_entry_a'],next_current_at_high_on_a=e['next_current_a'])
        rows.append(row);start=e['next_high_on_ns']
    if args.csv:
        with args.csv.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    stable=[r for r in rows if r['ring']>1]
    for phase in range(1,5):
        q=[r for r in stable if r['phase']==phase]
        print(json.dumps(dict(phase=phase,count=len(q),
          mean_high_off_commutation_ns=float(np.mean([r['high_off_to_low_on_ns'] for r in q])),
          mean_low_freewheel_ns=float(np.mean([r['low_freewheel_to_target_ns'] for r in q])),
          first_to_last_low_freewheel_change_ns=q[-1]['low_freewheel_to_target_ns']-q[0]['low_freewheel_to_target_ns'],
          mean_zvs_commutation_ns=float(np.mean([r['release_to_next_high_zvs_ns'] for r in q])),
          first_to_last_zvs_change_ns=q[-1]['release_to_next_high_zvs_ns']-q[0]['release_to_next_high_zvs_ns'],
          mean_handoff_ns=float(np.mean([r['full_handoff_ns'] for r in q])))))

if __name__=='__main__':main()
