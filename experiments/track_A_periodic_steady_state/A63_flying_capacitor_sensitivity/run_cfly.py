"""A63 - flying-capacitor sensitivity at fixed (A59-tuned) dead times, 250 W.

Usage:
    python3 run_cfly.py --design zvs --seed-json <A59 tuned point> --rise R --fall F --cfly-uf 3,2,1
"""
import argparse
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A62_load_sweep_fixed_deadtime"))
import variant_runner as V  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--design", required=True)
    p.add_argument("--seed-json", required=True)
    p.add_argument("--rise", type=float, required=True)
    p.add_argument("--fall", type=float, required=True)
    p.add_argument("--cfly-uf", required=True)
    a = p.parse_args()
    variants = []
    for token in a.cfly_uf.split(","):
        c = float(token) * 1e-6
        variants.append((f"C{float(token):g}uF", lambda b, c=c: replace(b, flying_capacitances_f=(c, c, c)), 250.0))
    V.run_variants(experiment="A63", runs_dir=HERE / "runs", design=a.design, seed_json=a.seed_json,
                   rise_ns=a.rise, fall_ns=a.fall, variants=variants)


if __name__ == "__main__":
    main()
