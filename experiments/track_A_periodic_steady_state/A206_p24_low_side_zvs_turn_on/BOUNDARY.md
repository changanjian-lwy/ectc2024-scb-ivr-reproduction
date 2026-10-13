# A206 - the low side's zero-voltage turn-on in the plant (V6), and the low sides' own turn-on resistance (BOUNDARY)
Method: mixed. Plant model change (cosim/gate.py, circuit.py; cfg-gated, off = bit-identical), single-edge harness
(a206_edge.py), cosim with the frozen RTL (cfg only), LTspice replays (scripts/p24_replay.py, EPC's model).
Track A, package layer. Written and committed before the registered runs. Looked at beforehand: A205's replays; the
harness against A205's LTspice numbers and one LTspice waveform, which shaped the model (Section 1); a 20 us smoke
run for timing only (V6 is 1.2 / 1.5 times slower than V5 with 0.3 / 3.0 ohm low sides).
Decision it changes: (1) whether the plant may be used for efficiency and for margins under about 3 A (A205: V5 may
not); (2) the low sides' turn-on resistance in the drive specification; (3) whether the binding rows hold 200 A.
Cheaper check done first: the single-edge harness (below).
Budget: stage 1 = 8 cosim runs (3.2 run-equivalents of 900 us, about 1.2 h) + 26 replays (about 20 min); stage 2 =
12 runs (7.7 run-equivalents, about 2 h).

## 1. What and why
- A205 (plant V5 against LTspice, nominal devices, 25 C): a settled period ends 3.5-6.8 A lower in LTspice and
  12.6 W of semiconductor loss per module are missing from the plant. Cause 1: the plant lets a low side conduct the
  instant it is commanded on at V_DS <= 0; through 3.0 ohm the gate needs several ns, with the device conducting in
  reverse meanwhile. Cause 2: the on-resistance sits in a lumped 0.54 mOhm per phase, not in the switches.
  A205's decision rule: the missing effects go into the plant before any other experiment.
- Plant V6 = V5 with three parts, each its own cfg switch:
  - gate "zvs_edge": a turn-on at V_DS <= 0 is an edge. The device's channel equation carries the reverse current
    (third quadrant, in place of the datasheet Fig. 8 fit at V_GS = 0) while the gate charges; the edge ends when
    |V_DS| <= 0.2 V with the gate above its channel start.
  - gate "miller": an off gate follows its charge balance while its drain moves. LTspice's waveform shows why: the
    falling node pulls the low side's internal gate to about -0.7 V just before its command (reverse drop 3.16 V,
    not the fit's 2.37 V), and the gate charges from there.
  - "r_sw_mohm" [high, low] with R = 0: a conducting switch position is a resistance of its own.
  Basis: the vendor's device model as run in LTspice (typical EPC2067, 25 C, 136 A through three devices, 5 V drive)
  and the datasheet's Fig. 8 (V_GS = 0, per device). No published measurement of this turn-on was looked up.
- Harness, 40 ns after a high-side turn-off at 136.4 A, low side commanded on 3.03 ns later (typical r_sw):
  | low-side turn-on | reverse volt-seconds: V6 / zvs_edge alone / LTspice (A205) | turn-on energy: V6 / LTspice |
  |---|---|---|
  | 3.0 ohm | 10.90 / 7.68 / 11.69-11.94 nVs | 1.56 / 1.61-1.70 uJ |
  | 1.0 ohm | 5.78 / 4.53 / 6.02-6.18 nVs | 0.83 / 0.81-0.89 uJ |
  | 0.3 ohm | 3.99 / 3.42 / 3.99-4.16 nVs | 0.57 / 0.51-0.60 uJ |
  Lowest V_DS 3.18 V against LTspice's 3.16 V. V5 on this edge: 0.2 nVs, no energy.
- Design variable: gate "r_on_ls", the low sides' own turn-on resistance: 3.0 (as specified so far), 1.0, 0.3 ohm.
- Stage 1, 25 C, nominal devices, A205's three cfgs. V runs (switches at the vendor model's typical 1.278 mOhm, as
  LTspice has): N0_steady, N0_step, N75_step at 3.0 ohm, N0_steady at 1.0 and 0.3 ohm, replayed in LTspice (A205's
  plan without the "zero" variants: 20 replays at 3.0 ohm, settled k 7-9 at 1.0 and 0.3 ohm). E runs (switches at
  the datasheet maximum 1.55 mOhm, the design basis of D62): N0_steady at 3.0 / 1.0 / 0.3 ohm, for loss and start-up.
- Stage 2, the binding rows of V5 on V6 with the chosen r_on_ls: +4.8 V / 1 us at 500 us + k T / 6 on N75 25 C,
  S75 0 C, S75 25 C (k 0, 2, 4), S75 125 C (k 1, 5), N0 25 C (k 0); end 80 us after the step.
- Known simplifications of V6: after the hand-over at 0.2 V the switch is at its full on-resistance (LTspice: about
  0.4 nVs more at 3.0 ohm); the device's series resistance is not in the edge (39 mV at 47 A); the off gate is
  followed in Python steps and at commands, a stretch the C loop runs through is taken as one linear ramp.
- Deviation from V5 in stage 2: r_sw follows the device temperature (maximum at 25 C times the vendor model's
  factor: 0.868 at 0 C, 1.581 at 125 C). V5's 0.54 mOhm did not.
- Not tested: slow or fast devices and other temperatures against LTspice, four modules, a closed loop in LTspice.
- The RTL is unchanged. Start-up: only ton_s may be re-trimmed (Section 4).

## 2. Criteria
 i1 scripts/cosim_regression.py --quick passes 4 / 4.
 i2 With the three parts off, A205's N0_steady cfg gives the archived record's sections to 160 us, bit for bit.
Stage 1, replays (LTspice minus plant, A205's limits):
 c0 start: phase currents within 0.05 A, flying-capacitor voltages and Vo within 5 mV (A205's c0 on state variables).
 c1 every peak within 2.0 A.
 c2 one period later: phase currents within 1.5 A, capacitor voltages within 20 mV, Vo within 0.5 mV.
 c3 every switch's largest V_DS within 1.5 V.
 c4 hard turn-ons: channel start within 0.3 ns, V_DS there within 1.0 V.
 c5 settled N0, first period: the plant's loss books (conducting switches, edges, reverse fit) within 10 % of
    LTspice's (channels and phase resistance), at 3.0, 1.0 and 0.3 ohm.
Stage 1 and 2, every cosim run (A194's absolute criteria):
 c6 COMPLETED, 0 shoot-throughs, 0 forced edges; peak <= 200 A over the whole run; V_DS <= 40 V; Vo <= 1.05 V up to
    300 us and within 1 V +- 50 mV from 20 us after the handover.

## 3. Predictions (not criteria)
- i1, i2 hold. c0 passes. c3 passes on 26 / 26. c1 passes on at least 22.
- c2: mode S 4 / 4; settled N0 passes at all three resistances (currents within 1.0 A); the step replays leave
  1-2.5 A on N75 and may miss.
- c4: mode S 4 / 4; settled, the later turn-ons now pass (they inherited the current difference): at least 18 / 26.
- c5: the plant 3-8 % below LTspice.
- Loss, settled N0, E runs against V5's 14.8 W: +11..+13 W at 3.0 ohm, +5..+7 W at 1.0 ohm, +3..+5 W at 0.3 ohm.
- The loop lengthens the on-time by about 0.9 / 0.4 ns (3.0 / 0.3 ohm); the settled peak stays within 2 A of V5's.
- Start-up (open-loop mode S loses the same volt-seconds): Vo before the handover 15-25 mV lower at 3.0 ohm and
  4-10 mV lower at 0.3 ohm than on V5; handover peak 180-200 A at 3.0 ohm, 168-178 A at 0.3 ohm (V5: 165.4 A).
- 0.3 ohm passes c6 and is chosen.
- Stage 2: N75 196-203 A, S75 at 0 C 195-203 A. A c6 miss on at least one of the twelve is as likely as not.

## 4. Decision rule
- i1 or i2 fails: fixed first; no V6 number is used.
- c2 and c5 pass at the three resistances: V6 is the plant for new claims, and the coverage file names the version of
  every figure. A miss: its cause is traced as in A205 and one more model round is allowed; a second miss is
  reported as the plant's stated error, and stage 2 runs with it.
- r_on_ls: the smaller of 0.3 and 1.0 ohm whose V and E runs pass c6. Neither: 3.0 ohm stays and its loss is the
  specification's stated price.
- Start-up: if the chosen value's E run misses c6 before 300 us, or its Vo at 143.5 us is more than 10 mV below
  V5's, ton_s is raised by that difference / 28.3 mV per ns (A155) and the E run repeated once, before stage 2.
- Stage 2: all pass: the binding rows are restated on V6 with their margins. A miss: reported as "the row does not
  hold on V6" with the record; a remedy is a new experiment, not part of A206.
