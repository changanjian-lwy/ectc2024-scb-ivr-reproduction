"""Check timing against the P24 four-phase equal-interleaving contract."""
import argparse,csv,json
from pathlib import Path
import numpy as np

def main():
    p=argparse.ArgumentParser();p.add_argument('interval_csv',type=Path)
    p.add_argument('--target-spacing-ns',type=float,default=50.)
    p.add_argument('--spacing-tolerance-ns',type=float,default=.05)
    args=p.parse_args();rows=list(csv.DictReader(args.interval_csv.open()))
    rows=[r for r in rows if int(r['ring'])>1]
    report=[]
    for phase in range(1,5):
        q=[float(r['full_handoff_ns']) for r in rows if int(r['phase'])==phase]
        mean=float(np.mean(q));dev=mean-args.target_spacing_ns
        report.append(dict(phase=phase,mean_spacing_ns=mean,
                           deviation_ns=dev,within_tolerance=abs(dev)<=args.spacing_tolerance_ns,
                           minimum_ns=min(q),maximum_ns=max(q)))
    print(json.dumps(dict(target_spacing_ns=args.target_spacing_ns,
                          tolerance_ns=args.spacing_tolerance_ns,
                          all_phases_pass=all(r['within_tolerance'] for r in report),
                          phases=report,
                          conclusion='total ring duration cannot substitute for individual phase spacing'),indent=2))
    if all(r['within_tolerance'] for r in report):raise SystemExit(0)
    raise SystemExit(2)

if __name__=='__main__':main()
