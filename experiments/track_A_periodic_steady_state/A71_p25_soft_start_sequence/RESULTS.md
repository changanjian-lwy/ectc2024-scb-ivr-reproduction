# A71 - zero start of the P25 three-phase SCB, following a published sequence (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`, with the Section 8
amendment (runs 4-6) made after runs 1-3 and before running them. Records:
- `run_*.json`: the section at every phase-1 high-side turn-on, plus
  valley firings;
- `a71_metrics.json`: the Section 6 metrics.

## 0. Verdict

**From an all-zero state, the idealised P25-scale SCB reaches D42's
4.9 mOhm periodic section when the published sequence is followed, with
one project-specific change.** The published sequence (Stillwell and
Pilawa-Podgurski 2019; Roberts' dissertation) is:
- fixed-timing switching from t = 0;
- the input ramped with the load disconnected;
- the load enabled at full input.

The change: the P25 current-sensed control takes over at the same moment
the load is enabled, not after a period of fixed-timing operation under
load.

| run | sequence | outcome |
|---|---|---|
| 5 | Roberts 30x ramp (457 us); load and handover together at 507 us | **reaches D42's section** 153 us after the handover; last section within 0.6 mA / 11 uV of `z*`; period 2172.366 ns |
| 6 | fast ramp (46 us); load and handover together at 96 us | **reaches D42's section** 101 us after the handover (same final state) |
| 2 | fast ramp; load at 96 us; handover 100 us later (196 us) | reaches D42's section (204 us after the handover) |
| 1 | Roberts ramp; load at 507 us; handover 100 us later (608 us) | **stalls** 11 us after the handover: Vo -0.23 V, all low sides on |
| 3 | P25 rule from t = 0, no fixed-timing start | **stalls** at 6 us, before the first cycle completes |
| 4 | fast ramp; load at 96 us; fixed timing kept to 496 us | fixed timing under load **settles into a sustained oscillation** (Section 2) |

The first and last cycles' valley firings are where the Chiang fallback
did its work:
- runs 5 and 6 fired 11 and 5 times, all within 27 us of the handover,
  at up to 3.4 V;
- none fired afterwards.

## 1. What each part of the sequence did

**Fixed-timing start, no load: works, and is necessary.**
- Run 3 shows why. With Vin ≈ 0, every wait-for-a-condition rule stalls:
  phase 2 waits for its low side's ZVS, and phase 1 waits for its -2.5 A
  current target.
- The published sequences all start under fixed timing, and so must this
  one.

**Series-capacitor tracking during the ramp** (ratio deviation from 2/3
and 1/3):

| Vin during the ramp | Roberts 30x ramp (457 us) | fast ramp (46 us) |
|---|---:|---:|
| 1-2 V | 0.169 | 0.486 |
| 2-4 V | 0.071 | 0.288 |
| 4-8 V | 0.030 | 0.209 |
| 8-12 V | 0.016 | 0.192 |
| peak phase current during the ramp | 32.7 A | 65.6 A |

After the ramp, with no load and full Vin:
- `VCs2/Vin` is 0.328-0.336 and Vo 1.047-1.049 V with the slow ramp;
- `VCs2/Vin` is 0.307-0.356 and Vo 0.90-1.13 V with the fast ramp.

Roberts' 30x-margin ramp therefore does what he says: the SCB's own charge
balance carries the ladder up with the input. The error shrinks as Vin
grows, and the peak current is half the fast ramp's. This is the one part
of Stillwell's FCML sequence that was not transferable by citation, and
here it is measured.

**The handover: must coincide with the load.**
- **Why P25 control and the load are matched.** Open loop, P25's control
  delivers ≈ 22.5 A per phase, i.e. the 67.5 A load. Enabling both at the
  same instant is matched from the start. From the calm no-load state,
  both runs 5 and 6 converge. Vo dips to 0.48 V (run 5) or 0.32 V (run 6),
  with peak currents of 57-58 A.
- **Why the later handover is unreliable.** Fixed timing under load never
  settles (Section 2), so a later handover lands on an arbitrary phase of
  a sustained oscillation.
  - Run 1 handed over at i2 = 51 A with i1 ≈ 0. Vo overshot to 2.0 V,
    then fell below zero. Phase 1's current target became unreachable,
    and the run stalled.
  - Run 2 happened to hand over at a benign phase.

## 2. A finding about fixed timing in this SCB

The SCB's own charge balance plus fixed timing is not enough under load:
- **No load:** fixed timing (T0 = 2 us, Ton 500 ns, 20 ns fixed dead time)
  is steady.
- **Under the 67.5 A load:** it falls into a sustained oscillation, not
  its period-1 steady state.
  - Run 4 shows `VCs2/Vin` peak-to-peak 0.205, 0.194, 0.194 and 0.194 in
    successive 100 us windows.
  - The phase currents' peak-to-peak at the sections is identical in the
    last three windows: 17.5 / 49.5 / 40.0 A. That points to a repeating
    limit cycle, not a slow decay.
  - Vo swings 0.38-1.05 V.
- **Why this is unexpected.** The linear series-capacitor mode (23 kHz)
  would decay with a ~12 us time constant through the 4.9 mOhm per phase,
  so something nonlinear sustains it.
- **The likely mechanism (not yet shown).** Under load, the current at
  the low-side turn-off hovers around zero, so the edge alternates between
  soft commutation and a hard turn-on after the 20 ns dead time. The
  effective duty then depends on the current. This is a hypothesis.

P25's event-timed control (mode P) has no such oscillation: it settles to
the D42 section. The finding says that, in this circuit, the event control
is what makes the loaded operating point steady.

## 3. Limits

- The circuit is A69's idealised one: linear Coss, ideal-diode reverse
  conduction, a constant-current load, open-loop Ton and ideal gate drive.
  The input is an ideal ramp; Stillwell's R_LIMIT path and auxiliary supply
  are not modelled.
- The handover rule, `t_dead` = 20 ns and T0 = 2 us are
  `PROJECT_DECISION`s. No source gives a handover into this control.
- With a real load, "Vo < 0" would be a brown-out, not a steady state. The
  stalls (runs 1 and 3) say that the controller can lose the operating
  point, not how hardware would behave afterwards.
- P24 (four phases, 48 V, 40 V devices) is not tested. There the input
  ramp needs Track B's precharge (Kim et al. 2018 on SCB start-up stress),
  and A67 says ZVS is out of reach, so the valley path is the steady-state
  turn-on.

## 4. Next

- **Mathematical model.** Add the valley trigger to the control memory
  (D06/D41). Check that the D41/D42 sections are unchanged, and that the
  A71 handover state (run 5's first mode-P section) is attracted.
- **Physical model.**
  - Repeat A71 on P24's four-phase circuit, with Track B's precharge
    and the valley path as the steady-state turn-on.
  - Look for the mechanism of the fixed-timing oscillation under load,
    e.g. by varying the dead time.

## 5. Reproduction

```
python3 a71_transient.py main_ramp457 --t-ramp 457 --t-load 507 --t-hand 607 --t-end 1207
python3 a71_transient.py fast_ramp46 --t-ramp 46 --t-load 96 --t-hand 196 --t-end 796
python3 a71_transient.py control_p25_from_t0 --t-ramp 457 --t-load 507 --t-hand 0 --t-end 1207
python3 a71_transient.py s_mode_loaded_400us --t-ramp 46 --t-load 96 --t-hand 100000 --t-end 496
python3 a71_transient.py handover_with_load_ramp457 --t-ramp 457 --t-load 507 --t-hand 507 --t-end 1107
python3 a71_transient.py handover_with_load_ramp46 --t-ramp 46 --t-load 96 --t-hand 96 --t-end 696
```

Wall time is ~1.2 s per simulated us.
