# A219 - LSCB's resistor pre-charge on the P24 module: a live 48 V bus, then a soft start (BOUNDARY)
Method: math (open-loop LTspice power stage, `scb_ivr.extensions.lscb_ladder`; plant = A180's, no controller).
Extension lscb_ladder. Written and committed before any run. Looked at beforehand: the paper (Sec. 2, Figs. 6, 9).
Decision it changes: whether the video (and the README) can say that LSCB's pre-charge would let a P24 module be
enabled on a live bus. P24's start (A180 su row; the cosim start-up alike) switches while Vin ramps from 0 V.
Cheaper check done first: none needed - every pre-charge row has all switches off and runs in seconds.
Budget: 9 runs, ~10 min at 2 jobs.

## 1. What and why
- LSCB: "a resistor-based pre-charging circuit is employed to initialize both DC and flying capacitors without
  incurring steady-state loss" (Fig. 6: 10 kOhm legs switched off by EN, diodes to the flying capacitors); measured as
  Vin ramps 0 -> 48 V. P24's switches (EPC2067) are rated 40 V.
- Pre-charge rows: every switch off while Vin ramps 0 -> 48 V in 10 us (pre_fast: a live bus connected) or 20 ms
  (pre_slow: a soft bus ramp), then 40 ms. Variants:
  - base: no network;
  - rdiv_pc: 4 x 1 kOhm divider across Vin and a 0.7 V diode from each divider node to a_k, no capacitors (the part P24
    could borrow without the ladder). 1 kOhm, not 10 kOhm, because Cs is 6 uF: tau ~5 ms; 1.2 mA while it is on;
  - lad_pc: the same with C_DC 4 x 20 uF.
- Soft start: switching starts at 48 V from the rdiv_pc pre_slow end state (and from the exact nominal state), on-time
  1 ns -> ton0 over 137.22 us (the length of A180's Vin ramp), full load, to 150 us; the network is switched out.
  Reference: A180's base su row again (Vin 0 -> 48 V in 137.22 us while switching at ton0), with the switch voltages.
- Not tested: breakdown physics (ideal switches, linear Coss), package loop (V_DS ringing), controller, the gate-drive
  supply at start-up, MLCC DC-bias derating, a hot-swap controller's own ramp.

## 2. Criteria
1. base pre_slow: SH1's largest voltage >= 40 V.
2. rdiv_pc pre_slow: every switch <= 16 V, and |Vcs - nominal| <= 1.0 V for all three at the end.
3. rdiv_pc pre_fast: SH1's largest voltage >= 40 V.
4. lad_pc pre_fast: every switch <= 20 V.
5. soft start from rdiv_pc pre_slow: largest phase peak <= su's + 10 A, and every switch <= 16 V.

## 3. Predictions (not criteria)
- base: SH1 -> ~48 V in both rows (switch nodes settle at the 0 V output through the inductors, Cs stay at 0).
- rdiv_pc: slow, SH1 12.5-15 V, Vcs end nominal - 0.7 +- 0.2 V; fast, SH1 ~48 V for 2-10 ms.
- lad_pc: fast 12-18 V (the string divides the edge, the diodes share charge into Cs); slow <= 14 V.
- soft from rdiv: peak within +-15 A of su's (A180: 166-169 A); switches <= 14 V. su again = A180's peaks.

## 4. Decision rule
- 1-3 pass: the video says P24's start needs the input to ramp with it, and a switched resistor divider (from LSCB)
  makes a module safe on a slowly ramped live bus, not on a hot-plug edge. 4 passes too: the capacitor ladder covers
  the edge as well.
- 5 passes: a pre-charged soft start is no worse than P24's ramped start - a candidate for a later cosim start-up
  experiment (the user's call).
- Any failure is reported as is. Extension only.
