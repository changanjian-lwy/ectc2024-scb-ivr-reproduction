"""A62 - load sweep at fixed (250 W-tuned) dead times, Vout regulated to 1 V.

Usage:
    python3 run_load_sweep.py --design zvs --seed-json <A59 tuned point> --rise R --fall F --powers 250,200,150,100,50,25
"""
import argparse
from dataclasses import replace
from pathlib import Path

import variant_runner as V

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--design", required=True)
    p.add_argument("--seed-json", required=True)
    p.add_argument("--rise", type=float, required=True)
    p.add_argument("--fall", type=float, required=True)
    p.add_argument("--powers", required=True)
    a = p.parse_args()
    variants = []
    for token in a.powers.split(","):
        watts = float(token)
        variants.append((f"P{watts:g}W", lambda b, w=watts: replace(b, module_power_w=w), watts))
    V.run_variants(experiment="A62", runs_dir=HERE / "runs", design=a.design, seed_json=a.seed_json,
                   rise_ns=a.rise, fall_ns=a.fall, variants=variants)


if __name__ == "__main__":
    main()
