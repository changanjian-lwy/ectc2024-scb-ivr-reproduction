"""Build a declared Coss sensitivity sweep from the aligned local 2% case."""

from pathlib import Path

TRACK = Path(__file__).resolve().parent
SOURCE = TRACK / "A31_p24_local_il2_2pct_event_alignment" / "A31_p24_local_il2_2pct_event_alignment.cir"

for scale in (0.05, 0.10, 0.25, 0.50, 0.75):
    tag = str(scale).replace(".", "p")
    name = f"A32_coss_scale_{tag}_p24_local_2pct"
    out = TRACK / name
    text = SOURCE.read_text()
    text = text.replace("* A31 - A28 with derived local iL2 event-alignment seed",
                        f"* A32 - A31 with declared Coss scale {scale}", 1)
    anchor = ".param VIN=48"
    if text.count(anchor) != 1:
        raise SystemExit("A31 parameter anchor changed")
    text = text.replace(anchor, f".param COSS_SCALE={scale}\n{anchor}", 1)
    text = text.replace("CH1_TOTAL vin a1 {CH_TOTAL}", "CH1_TOTAL vin a1 {COSS_SCALE*CH_TOTAL}")
    text = text.replace("CL1_TOTAL x1 g {CL_TOTAL}", "CL1_TOTAL x1 g {COSS_SCALE*CL_TOTAL}")
    text = text.replace("CH2_TOTAL a1 a2 {CH_TOTAL}", "CH2_TOTAL a1 a2 {COSS_SCALE*CH_TOTAL}")
    text = text.replace("CL2_TOTAL x2 g {CL_TOTAL}", "CL2_TOTAL x2 g {COSS_SCALE*CL_TOTAL}")
    text = text.replace("CH3_TOTAL a2 a3 {CH_TOTAL}", "CH3_TOTAL a2 a3 {COSS_SCALE*CH_TOTAL}")
    text = text.replace("CL3_TOTAL x3 g {CL_TOTAL}", "CL3_TOTAL x3 g {COSS_SCALE*CL_TOTAL}")
    text = text.replace("CH4_TOTAL a3 x4 {CH_TOTAL}", "CH4_TOTAL a3 x4 {COSS_SCALE*CH_TOTAL}")
    text = text.replace("CL4_TOTAL x4 g {CL_TOTAL}", "CL4_TOTAL x4 g {COSS_SCALE*CL_TOTAL}")
    out.mkdir(exist_ok=True)
    (out / f"{name}.cir").write_text(text)
    (out / "BOUNDARY.md").write_text(f"""# A32 Coss sensitivity boundary

- Parent: A31 local 2% event-aligned diagnostic.
- Only changed electrical input: all device commutation capacitances are
  multiplied by {scale}.
- This is a sensitivity point, not a sourced GS61008T value and not a fit.
- Purpose: bracket the maximum constant effective Coss compatible with the
  local P24 2% commutation mechanism under the otherwise fixed A31 state.
""")
    print(out / f"{name}.cir")
