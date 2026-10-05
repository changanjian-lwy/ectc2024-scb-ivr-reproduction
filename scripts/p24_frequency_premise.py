"""D67: D64's stripline frequency choice rerun at 2.5 MHz and at P24 Fig. 5's footprint per phase.

    python3 scripts/p24_frequency_premise.py

D64's script (scripts/p24_frequency_choice.py) with f = 1 / 2 / 2.5 / 3 / 5 MHz and footprints 0.25 cm^2 (one 2.5 mm x
10 mm column of a 10 mm module, Fig. 5b) and 0.625 cm^2 (the 25 x 40 mm package over 16 phases) next to D64's 1 and
2 cm^2. Nothing else changes. Writes symbolic_derivations/03_P24_native/diagnostics/D67_frequency_premise.json.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("d64_choice", ROOT / "scripts" / "p24_frequency_choice.py")
D64 = importlib.util.module_from_spec(spec); spec.loader.exec_module(D64)
D64.FREQS = (1.0, 2.0, 2.5, 3.0, 5.0)
D64.AREAS = (0.25e-4, 0.625e-4, 1e-4, 2e-4)
D64.OUT = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics" / "D67_frequency_premise.json"

if __name__ == "__main__":
    D64.main()
