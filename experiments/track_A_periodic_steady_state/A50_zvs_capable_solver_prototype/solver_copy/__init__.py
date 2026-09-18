"""A50 local, import-path-isolated copy of the parallel math model's solver.

Per `../BOUNDARY.md` Section 0, this package is a byte-for-byte copy of seven
`src/scb_ivr/` modules (first commit), subsequently extended IN THIS COPY ONLY
with switch capacitance and a genuine three-state per-phase dead-time mode.

`src/scb_ivr/` is never written to by this experiment, and this package never
imports from it: the only edit applied to the copied files on import grounds
was rewriting ``from scb_ivr.X import ...`` into the package-relative
``from .X import ...``.  Importing this package therefore pulls in nothing
under `src/scb_ivr/`, which the A50 test scripts assert directly by inspecting
``sys.modules`` after import.
"""

from __future__ import annotations

__all__ = [
    "commutation_capacitance",
    "commutation_feasibility",
    "device_library",
    "evidence",
    "periodic_affine_solver",
    "zero_start_descriptor",
    "zero_start_hybrid_solver",
]
