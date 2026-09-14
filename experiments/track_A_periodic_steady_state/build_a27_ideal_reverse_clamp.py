"""Build A27 by adding the P25-required ideal GaN reverse paths to A26."""

from pathlib import Path


TRACK = Path(__file__).resolve().parent
SOURCE = TRACK / "A26_h2_zvs_readiness_guard" / "A26_h2_zvs_readiness_guard.cir"
OUTDIR = TRACK / "A27_ideal_gan_reverse_clamp"
OUTPUT = OUTDIR / "A27_ideal_gan_reverse_clamp.cir"

text = SOURCE.read_text()
anchor = ".include ../../../paper_locked/04_component_models/GS61008T_commutation_capacitance.lib"
if anchor not in text:
    raise SystemExit("A26 include block no longer matches A27 builder")
text = text.replace(
    "* A26 - A25 plus phase-2 Vds-zero readiness guard",
    "* A27 - A26 plus ideal GaN off-state reverse-conduction paths",
    1,
)
text = text.replace(
    anchor,
    anchor + "\n.include ../../../paper_locked/04_component_models/GaN_reverse_conduction_ideal.lib",
    1,
)

replacements = {
    "SH1 vin a1 gh1 g SWH": "SH1 vin a1 gh1 g SWH\nDH1_REVERSE a1 vin DGAN_IDEAL",
    "SL1 x1 g gl1 g SWL": "SL1 x1 g gl1 g SWL\nDL1_REVERSE g x1 DGAN_IDEAL",
    "SH2 a1 a2 gh2 g SWH": "SH2 a1 a2 gh2 g SWH\nDH2_REVERSE a2 a1 DGAN_IDEAL",
    "SL2 x2 g gl2 g SWL": "SL2 x2 g gl2 g SWL\nDL2_REVERSE g x2 DGAN_IDEAL",
    "SH3 a2 a3 gh3 g SWH": "SH3 a2 a3 gh3 g SWH\nDH3_REVERSE a3 a2 DGAN_IDEAL",
    "SL3 x3 g gl3 g SWL": "SL3 x3 g gl3 g SWL\nDL3_REVERSE g x3 DGAN_IDEAL",
    "SH4 a3 x4 gh4 g SWH": "SH4 a3 x4 gh4 g SWH\nDH4_REVERSE x4 a3 DGAN_IDEAL",
    "SL4 x4 g gl4 g SWL": "SL4 x4 g gl4 g SWL\nDL4_REVERSE g x4 DGAN_IDEAL",
}
for old, new in replacements.items():
    if text.count(old) != 1:
        raise SystemExit(f"A26 device anchor mismatch: {old}")
    text = text.replace(old, new, 1)

OUTDIR.mkdir(exist_ok=True)
OUTPUT.write_text(text)
print(OUTPUT)
