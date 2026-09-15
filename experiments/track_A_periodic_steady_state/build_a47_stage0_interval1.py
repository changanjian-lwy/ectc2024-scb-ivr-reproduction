"""Generate A47's stage-0 (P24 interval 1) netlist.

A47 studies whether replacing the constant-capacitance GS61008T Co(tr)
commutation-capacitance model with a digitized, fitted NONLINEAR Coss(V)
model moves A42's zero-snubber local ZVS threshold, and whether it helps
close the gap toward the 2024 paper's literal 1%-2% negative-current range
(see BOUNDARY.md; A46 found the constant-capacitance model needs an
effective capacitance 1-2 orders of magnitude smaller than either device's
constant Co(tr) to reach 1%-2%, which nonlinear Coss(V) -- much larger near
Vds=0 -- might partially explain).

Interval 1 (R04D0) has no CH1/CL1 commutation-capacitance element at all
(see paper_locked/02_ectc2024_main/spice/R04D0_p24_first_interval_shared_ladder.cir):
only the switches, flying capacitor and inductor. Its result is therefore
mathematically independent of whether the downstream commutation-capacitance
model is constant or nonlinear-in-V. This stage is still rebuilt and rerun
byte-for-byte (only the header comment changes), exactly as A45 stage 0 did,
so the full interval-1->2->3 chain is verifiably re-run for A47 rather than
silently re-using R04D0's committed output numbers.
"""

from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
TRACK = Path(__file__).resolve().parent
PARENT = (
    PROJECT / "paper_locked/02_ectc2024_main/spice/"
    "R04D0_p24_first_interval_shared_ladder.cir"
)
OUT = (
    TRACK
    / "A47_nonlinear_coss_local_zvs"
    / "A47_stage0_interval1_shared_ladder.cir"
)

HEADER_OLD = (
    "* R04D0 - P24 first interval on the shared Fig.3 flying-capacitor ladder"
)
HEADER_NEW = (
    "* A47 stage 0 - P24 interval 1, re-run unchanged from R04D0\n"
    "* This stage has no CH1/CL1 commutation-capacitance element, so it is\n"
    "* mathematically identical regardless of the constant-Co(tr) vs nonlinear-\n"
    "* Coss(V) choice made downstream in A47 stage 1/2. Rerun here only for the\n"
    "* required full-chain provenance trail (see A47 BOUNDARY.md); its output\n"
    "* is expected to reproduce R04D0's committed IL1_MAX/VC1_END/IL2_AT_TON\n"
    "* values exactly (as A45 stage 0 already confirmed for a different\n"
    "* device-swap experiment) and that reproduction is checked, not assumed."
)


def build() -> Path:
    text = PARENT.read_text()
    assert HEADER_OLD in text, "R04D0 header text changed; update this script"
    text = text.replace(HEADER_OLD, HEADER_NEW, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    return OUT


if __name__ == "__main__":
    print(build())
