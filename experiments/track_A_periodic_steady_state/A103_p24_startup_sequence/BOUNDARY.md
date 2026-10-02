# A103 / D58 - the P24 module's start-up sequence (BOUNDARY)

Track A, main line (the reproduction's own controller; no added hardware).

**Written before any A103 run.** The code change (bridge keys `t_load_us`,
`t_hand_us`; `--full` regression PASS), D58 and the predictions
(`d58_predictions.json`) are committed with this file.

## 1. Question

The adopted design's start-up reaches **1.277 V at the handover
(88.6 µs), dips to 0.903 V and settles by about 170 µs** (A100's reference
run; A101's ref is identical).

**Can the sequence alone fix this, without new hardware or RTL?**

## 2. Prior work

- **Series capacitors (the ladder).**
  - Roberts' dissertation (Ch. 3.5) ramps the input at a rate set by the
    capacitors' resonance, with the converter switching.
  - The 68.61 µs ramp is his 30x margin at 3 µF
    (`paper_locked/00_boundaries/ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`).
  - A71-A73 showed that this, fixed-timing mode S during the ramp, and
    load plus handover together reach the periodic state.
  - **This part is kept.**
- **Intel VRD 11.1** (Processor Power Delivery Design Guidelines, 2009,
  public):
  - Sec. 1.4.4: a soft start is required (default 500 µs ramp);
  - Sec. 1.4.2: the PWM regulates to Vboot after the ramp;
  - Sec. 1.9.1: VR_READY marks the sequence complete, and processor reset
    and other rails are sequenced from it;
  - Sec. 1.3.7, Table 1-5: overshoot at most VID + 50 mV, and at most
    25 µs above VID.
- **Recent VR13/VR14 controllers** (Infineon XDPE15284D, 2022; TI
  TPS536C9) list start-up into a pre-bias and a controlled output slew.
  This is from their product summaries; the datasheets were not read in
  full.
- **What none of these give:** the P24 module's own sequence. P24 and P25
  describe no start-up of the output.

## 3. Diagnosis (D58, before any run)

D58 is an averaged model (`symbolic_derivations/03_P24_native/D58_P24_STARTUP_AVERAGED.md`):
- **Mode S** (open loop) is a voltage source behind 1.47 mΩ.
- **Mode P** (boundary conduction with a fixed negative-current target) is
  a current source set by Ton: per phase (V_rail − Vo) Ton / (2L) − i_neg,
  whatever the period.
- **The integral loop** is A79's, once per period.

**Validation.** On the reference start-up it is within 0.03 V of the
co-simulation everywhere and within 15 LSB in Ton (minimum 0.883 against
0.903 V).

**What it shows:**
1. **The overshoot is mode S at no load:** open loop, 1.277 V at full
   input.
2. **The dip is the load step at the handover.** The loop starts at Ton
   533 with Vo at 1.277 V, so Ton first falls to 455. Meanwhile the 250 A
   load discharges Co with Co·R = 18.7 µs.
3. **Mode P cannot run at light load.** At the lower clamp (0.5 × Ton) it
   still delivers about 100 A. A no-load closed-loop soft start, then load
   at VR_READY, is therefore not possible with this controller. That is a
   light-load question, outside this single-module, full-load level.
4. **A pre-biased reference ramp** after the handover lowers the peak
   (2-9 mV) but not the time above 1 V (~60 µs). That tail is the voltage
   loop's own slowness (scorecard T6), not the sequence.

## 4. Cases (co-simulation)

**Physical model:** Verilog RTL (unchanged) with A88's plant (kernel2) and
the adopted design (A92's correctors, A97's averaged slots), 5%, 25 C,
4 mΩ resistive load, 500 µs, records of 6000 edges.

| run | load | handover | mode S Ton |
|---|---|---|---|
| c0_reference | at 88.61 µs | 88.61 µs | 533 LSB (16.667 ns) |
| c1_load_from_0 | from t = 0 | 88.61 µs | 533 |
| c1b_load_from_0_hand_72 | from t = 0 | 72 µs | 533 |
| c1d_load_from_0_hand_72_ton568 | from t = 0 | 72 µs | 568 (17.75 ns; the loop's initial value and clamps follow) |

**The load from t = 0** stands for a processor's reset leakage: resistive,
current proportional to Vo. A full 4 mΩ from the start is the worst case
of that.

## 5. Registered criteria and predictions

From `d58_predictions.json`:

| run | Vo max (time) | Vo at the handover | min after the handover | within 1% from | time above 1 V |
|---|---|---|---|---|---|
| c0 | 1.269 V (88.6 µs) | 1.269 | 0.883 | 205.9 µs | 43 µs |
| c1 | 1.011 V (147.5 µs) | 0.932 | 0.932 | 156.2 µs | 60 µs |
| c1b | 1.018 V (125.2 µs) | 0.898 | 0.898 | 145.5 µs | 60 µs |
| c1d | 1.013 V (112.1 µs) | 0.957 | 0.957 | 125.2 µs | 61 µs |

**Criteria:**
1. **No overlap.**
   - The peak V_DS and phase current stay within the reference's (24.8 V
     and its current peak) or are explained.
   - The ladder deviation before the handover is ≤ 3% (A73).
2. **Against D58** (all four runs):
   - Vo max within ±15 mV, its time within ±15 µs;
   - Vo at the handover and the minimum after it within ±0.03 V;
   - the 1% settling time within ±20 µs.
3. **VRD 11.1** (c1, c1b, c1d):
   - Vo max ≤ 1.050 V;
   - the time above 1 V is reported against 25 µs. **D58 predicts it is
     missed** (~60 µs, the loop's tail).
4. **The same final state as c0** (last 200 periods):
   - Vo within ±3 mV (the loop wanders by ±2 mV);
   - per-phase high-side turn-on V_DS within ±0.1 V;
   - low-side turn-on V_DS ≤ 0;
   - turn-off currents within ±0.5 A.

## 6. What stays assumed

- **The boot load:** full 4 mΩ from t = 0. A processor's real reset
  current is not known here.
- **Light-load start** (VR_READY, then load) needs a light-load mode.
  Not this level.
- **25 C, no jitter, the 5% target.**
