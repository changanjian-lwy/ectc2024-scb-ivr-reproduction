# A205 - the plant against LTspice over whole periods (RESULTS)
Boundary: ec33c6c (registered as A199). Records: release records-a205 (three cosim records, logs); the 29 replay
comparisons are in replays/ (numbers only). Analysis: a205_analyze.py -> a205_summary.json. Tool:
scripts/p24_replay.py at e4a9952. Plant V5, final configuration, nominal devices, 25 C, one module. LTspice: EPC's
EPC2067 model on all 20 switches, started from the plant's state, same gate commands, two periods per replay.
Identity: the N0 records' sections equal A194 r20's (made before the snapshot code) up to 296.9 / 499.9 us; the N75
rerun equals its first record. cosim_sources_modified False.

## 0. Verdict
- **What agrees.**
  - The plant's largest peaks, replayed from the snapshot at the peak: 182.7 against 182.8 A (N0, +4.8 V / 1 us) and
    198.35 against 198.52 A (N75). The first peak of every replay is within 0.17 A.
  - Hard switching. In mode S (every turn-on hard, 200 ns period) c1-c4 all pass: channel start within 0.024 ns,
    V_DS there within 0.14 V, the one-period state within 1.1 A. Settled, each phase's first turn-on is within
    0.11-0.19 ns.
  - V_DS: c3 passes on all 23. LTspice's maxima lie -1.46..+1.14 V from the plant's and reach 32.3 V at most.
- **What does not: c2 fails on the 19 replays outside mode S.** One period later, with the same commands, three of
  the four phase currents are 3.5-5.0 A (N0) or 4.5-6.8 A (N75) below the plant's and Vo is 1.1-1.4 mV lower.
  Registered prediction: 2-5 A.
- **Traced causes** (the currents at every edge, settled N0):
  1. **The low side's turn-on.** The plant makes it conduct the instant it is commanded on at V_DS <= 0 (its
     reverse-conduction time is 0.003 ns per period). In LTspice the gate needs about 10 ns through 3.0 ohm, and
     until then the device conducts in reverse at up to 2.8 V: 11.8 nVs per turn-on against the plant's 2.9 nVs,
     3.3 A. Diagnostic replays with the low sides' turn-on resistance at 1.0 / 0.3 ohm in LTspice: 6.1 / 4.1 nVs;
     at 0.3 ohm a turn-on costs 0.5 A.
  2. **The high side's on-time**: 1.3-1.5 A less per on-time whatever the low-side resistor. Part is where the
     resistance sits. The plant spreads a duty-weighted 0.54 mOhm over the period; in the circuit an on-time's path
     holds the high side (0.64 mOhm) and the previous phase's low side (0.43 mOhm). About 0.8 A is not traced.
- **Consequence 1, loss.** Semiconductor loss over the first period, settled N0: LTspice 27.4 W (high sides 3.7,
  low sides 21.5, phase resistance 2.2) against 14.8 W in the plant's books (12.3 conduction, 2.4 edges, 0 reverse
  conduction). **12.6 W per module are missing from the plant**, about 10 W of them the low sides' reverse
  conduction at turn-on (the 40 ns after each high-side turn-off hold 12.9 W, 6.6 / 4.2 W with 1.0 / 0.3 ohm on the
  low sides). With 1.0 / 0.3 ohm the gap is 6.3 / 4.0 W. As efficiency (Pout / (Pout + Ploss),
  250 W): about -4 points with the specified 3.0 ohm on the low sides, about -1.3 points with 0.3 ohm.
- **Consequence 2, peaks.** With the same commands phase 1's next peak is 1.1 A (settled), 1.5 A (N0 step) and
  2.7 A (N75 step) higher in LTspice: 200.5-201.3 A where the plant has 197.8-198.5 A. The valley before it is
  3.3-4.7 A deeper in LTspice, the node finishes its swing earlier, and the on-time is in effect longer.
  A closed loop would react to the deeper valley; where it settles cannot be read from open-loop replays. **The
  margins at the binding rows, 1.5 A (N75) and 2.2 A (S75), are smaller than this difference.**
- **Consequence 3, the specification.** It gives "3.0 ohm on" to every switch. The low sides turn on at zero voltage
  and gain nothing from a slow gate, and the plant could not see what it costs. The low sides need their own, small
  turn-on resistance; their rare hard turn-ons then have to be checked.
- By the decision rule, both effects go into the plant (cfg-gated) and the binding rows and the efficiency are
  rerun with it before any other experiment. At fixed commands the loss of volt-seconds is 2.3 % of an on-time's
  (13.4 A per period in total), so a loop would lengthen the on-time by about 0.9 ns (0.5 ns with 0.3 ohm).

## 1. Criteria (LTspice minus plant; 23 replays)
| group | n | c1 peaks <= 2.0 A | c2 one period | c3 V_DS <= 1.5 V | c4 hard turn-on | numbers |
|---|---|---|---|---|---|---|
| mode S, N0 | 4 | 4 | 4 | 4 | 4 | peaks -0.5..+1.6 A; currents -0.3..-1.1 A; Vo -0.11 mV; V_DS 1.14 V; 0.024 ns / 0.14 V |
| settled, N0 | 6 | 6 | 0 | 6 | 0 | peaks -1.9..+1.2 A; currents +1.2 / -4.7..-5.0 A; Vo -1.13 mV; V_DS 1.22 V |
| settled, N0, "zero" | 3 | 0 | 0 | 3 | 0 | peaks -2.03..+0.7 A; currents +0.8 / -3.8..-4.6 A; Vo -0.96 mV |
| N0 step, at the step | 2 | 2 | 0 | 2 | 0 | as settled |
| N0 step, at the peak | 3 | 0 | 0 | 3 | 0 | first peak -0.13 A; later -4.6..+1.6 A; currents +1.7 / -3.5..-4.9 A |
| N75 step, at the step | 2 | 0 | 0 | 2 | 0 | peaks -2.14..+2.13 A; currents +2.1 / -5.9..-6.3 A |
| N75 step, at the peak | 3 | 0 | 0 | 3 | 0 | first peak -0.17 A; later -6.7..+2.7 A; currents +2.9 / -4.5..-6.8 A |
| **all** | 23 | 12 | 4 | 23 | 4 | |
- **c0 fails on all 23 as written, and could not pass.** Phase currents arrive within 0.004 A, but node voltages are
  47-90 mV off at the start. A conducting switch has no drop in the plant and I x R_DS(on) in a device, and the
  1 mOhm hold carries that switch's current. The criterion should have been written on the state variables
  (currents, capacitor voltages). It was mine and it was wrong; nothing else depends on it.
- c4 outside mode S fails on later turn-ons, which inherit the current difference (up to 2.4 V, 0.37 ns; after the
  step, turn-ons at V_DS near zero make "channel start" the current's reversal and differ by up to 6.6 ns).
- Mode S loss: LTspice 79.5 W against 66.0 W booked (9.9 + 40.2 + 15.8 reverse conduction).

## 2. Faults of the tool, found and fixed during the replays (BOUNDARY Section 4)
1. LTspice switch elements in the gate branches collapsed the time step below 1 fs within 5-100 ns. The drivers
   are now one behavioural current source each (ca588bd). A two-period replay takes 35 s.
2. **LTspice gives every inductor 1 mOhm in series by default, twice the plant's phase resistance.** The first pass
   of all 23 replays showed 10-14 A per period, in the predicted direction. Adding up dI = (V_x - V_out - R i) / L
   over each interval left 3.2 A unexplained, which was that resistance (fixed e4a9952). The first pass is discarded.
3. The N75 record has two interlock holds (1.4 ns, SH4, at 519.9 and 520.8 us). The gate model now logs holds and
   the replay reproduces them (adb3a56); both lie outside the replay windows.
4. The number: registered as A199 while another session had taken A199-A204; renumbered before these results.

## 3. Predictions
- Held: c3; c4 in mode S; c2 fails with LTspice below the plant (4.5-6.8 A against 2-5 A predicted, of which the
  named cause gives 3.3 A); the first peak within 0.5 A; "zero" within 1 A of "match" (0.4-0.9 A).
- Missed: c0; c4 settled (predicted to pass); the on-time's 1.3-1.5 A was not foreseen.

## 4. Limits
- Nominal devices at 25 C only. Slow and fast devices, other temperatures and four modules are not replayed.
- Open loop over two periods. Loss and current differences are for the first period after a plant state; LTspice's
  own periodic state, and a closed loop on it, are not computed. The efficiency figures are estimates from that.
- LTspice with the vendor's typical model is a second model, not hardware.
