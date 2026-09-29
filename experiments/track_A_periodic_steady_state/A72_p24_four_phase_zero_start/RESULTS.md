# A72 - the A71 start-up sequence on P24's four-phase module (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`. Amendments:
- Section 8 (runs 4-8), made after runs 1-3;
- Section 9 (runs 9-10), made after runs 4-8.

Each amendment was written before its runs. Records:
- `run_*.json`;
- `a72_summary.json`;
- `regression_gate_vs_A71.json`.

## 0. Verdict

**The sequence that worked on the P25-scale three-phase SCB (A71) does not
carry over to P24's four-phase module.** The failure has two independent
causes, and both point to the same requirement: the series-capacitor
ladder must be **precharged** before switching hands over.

1. **The input ramp alone does not balance P24's ladder, and the switches
   exceed their rating.**
   - Under fixed timing, with Roberts' 30x ramp (68.61 us), the ladder
     ratios deviate by up to 0.46-0.49 from (3/4, 1/2, 1/4) once
     Vin ≥ 12 V.
   - The peak phase current is 427-510 A, and the switch Vds reaches
     47.6-47.9 V, against EPC2067's 40 V rating.
   - This holds in all four cells of the factorial: dead time 2.15 or
     0.05 ns, load on or off during the ramp (runs 4-7).
   - Track B's LTspice netlist is different (no dead time, no Coss,
     input parasitics), yet it also ends unbalanced with the ramp alone.
     R04E16: VCs 19.9 / 13.2 / 6.6 V against 36 / 24 / 12 V, Vo 0.56 V.
     Only R04E17's divider precharge reached 35.8 / 23.8 / 11.9 V and
     Vo 1.006 V.
2. **P25's single-sensor control cannot rebalance a badly unbalanced P24
   ladder.**
   - From the ramp-only state, mode P either stalls (runs 1, 2, 8) or,
     with the fixes below, keeps running without converging (runs 9-10):
     Vo 0.02-0.41 V, currents up to ~1 kA, Vds 48.4 V.
   - One degenerate pattern recurs. With VCs1 ≈ VCs2 ≈ Vin, phase 1's
     node gets almost no volt-seconds, so its cycle collapses to ~65 ns.
     Phases 2-4 are timed from phase 1's turn-on (+50/+100/+150 ns), so
     they starve.

By contrast, P25's three-phase ladder tracked the ramp (A71: within 1.6%
over 8-12 V). That is a real difference between the local (P25) and the
global (P24) case, not a coding artefact. The generalised code reproduces
A71 bit for bit at N = 3 (Section 3).

## 1. Runs

| run | sequence | outcome | peak i | peak Vds |
|---|---|---|---:|---:|
| 1 | 30x ramp; load and handover at 88.61 us | stalled at 107 us (the window was too tight: false stall) | 459 A | 47.6 V |
| 2 | 3x ramp; load and handover at 26.9 us | stalled at 68.9 us: phase 2 waiting with i2 = +109.5 A (no resonance) | 463 A | 47.7 V |
| 3 | mode P from t = 0 | stalled at 0.6 us | - | - |
| 4-7 | mode S only; dead time {2.15, 0.05} ns x load {off, on} | ladder unbalanced in every cell (deviation 0.46-0.49) | 427-510 A | 47.6-47.9 V |
| 8 | run 1 with a 20*T0 stall window | mode P pulled the ladder to 0.747 / 0.500 / 0.261 (see below) | 459 A | 47.6 V |
| 9 | run 8 + level-sensitive events + restart timers | ran to the end without settling | 1166 A | 48.2 V |
| 10 | run 2 + the same fixes | ran to the end without settling | 958 A | 48.4 V |

**Run 8 in detail.** Before failing, mode P pulled the ladder to
0.747 / 0.500 / 0.261 with Vo 0.955 V.
- The high sides then turned on by the valley path on almost every edge:
  ~4 firings per cycle, at Vds ~10 V. That is exactly what A67 predicts
  at P24's point, where ZVS is out of reach.
- The state was not steady: a phase-4 section current crept up by
  ~0.65 A per cycle.
- A hard valley turn-on at 18.7 V then upset it. Vo went to -0.34 V, and
  the run stalled at 190 us.

## 2. Controller-implementation findings

Both were found here and fixed behind flags; the defaults reproduce runs
1-8.

1. **Level-sensitive detection.**
   - The inherited event detection (A69-A71) fired only on a crossing. A
     condition already met on entering a state never fired: e.g. i1 =
     -265 A at the start of phase 1's wait for -2.5 A.
   - A comparator-based controller is level-sensitive. With
     `level_events`, such a condition fires at once.
   - **Effect on A69-A71.** Their converged runs cannot contain a missed
     event, because a missed event always ends in a stall. Of their
     stalled runs, A71 run 3 (P25 rule from t = 0) may have had phase 2
     waiting on an already-met ZVS condition. Its phase 1 was in a genuine
     wait (i1 = -0.02 A against -2.5 A at Vo ≈ 0), so it would have
     stalled anyway. A70 run 4 and A71 run 1 stalled in genuine waits
     (i1 above its target).
2. **Restart timers.**
   - When the current at a timed low-side turn-off is positive, the
     low-side diode clamps the node. There is no resonance, hence neither
     ZVS nor a valley (run 2).
   - Published valley/ZCD-triggered controllers carry a restart timer
     for this case: TI UCC28051 (gate forced on after 400 us nominal off
     time) and UCC28063A (an on-time generated if no ZCD edge within
     165-265 us).
   - Added as `CROSS_PAPER_EXTENSION`, with values as `PROJECT_DECISION`:
     - 20 ns on the UP and DOWN waits;
     - 400 ns on phase 1's current-target wait.

With both fixes the controller never stalls (runs 9-10). What it cannot do
is recover the P24 ladder from a badly unbalanced state.

## 3. Checks

- **Regression gate (BOUNDARY Section 4).** With N = 3, P25 values and a
  constant-current load, the generalised code reproduces the first 30 us
  of A71 run 6 bit-identically: 16 sections, 0.0 difference.
- **After the Section 9 code change.** The gate was rerun with default
  settings: still bit-identical.

## 4. Limits

- The circuit is idealised: linear Coss (1860 pF per device), 0.54 mOhm
  lumped per-phase resistance, 0.1 uOhm switches and diodes, an ideal
  input ramp, and open-loop Ton.
  - Cout = 4.672 mF is inherited and suspect.
  - Cfly = 3 uF is Track A/B's first-principles value.
- Peak currents and voltages depend on the damping model: they differ
  from Track B's (86.9 A peak in R04E16). The qualitative outcome, "the
  ramp alone does not balance the ladder", agrees across both models.
- The restart-timer values, `t_dead`, T0 and the handover rule are
  `PROJECT_DECISION`s.
- The mathematical model is three-phase P25-native. Whether P24's mode-P
  orbit exists and is stable (the run-8 drift) is a structural question
  that this physical model only hints at.

## 5. Next

1. **Precharge first (physical model).** Build Track B's R03A/R02B
   passive divider precharge (CDIV = 300 uF, as in R04E17) into this
   simulator. Repeat: precharge, then the 30x ramp, then the load and
   handover together, with the level-sensitive events and the restart
   timers.
   - Check Vds < 40 V throughout.
   - Check whether mode P settles from a balanced ladder.
   - Literature on flying-capacitor precharge not yet read:
     - Janik et al., IECON 2013, DOI 10.1109/IECON.2013.6700175 (four-level
       FCC precharge);
     - Thielemans et al., IECON 2009, DOI 10.1109/IECON.2009.5415024
       (self-precharge).
2. **P24 mode-P orbit (mathematical model, structural).** The run-8 drift
   suggests the P24 operating point may be weakly unstable at 0.54 mOhm
   damping, as D41's lossless P25 orbit was. That needs the four-phase
   extension of the event model, or a shooting/Floquet check in this
   simulator.

## 5a. Reproduction

```
python3 a72_transient.py main_ramp68p61 --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61
python3 a72_transient.py fast_ramp6p861 --t-ramp 6.861 --t-load 26.861 --t-hand 26.861 --t-end 326.861
python3 a72_transient.py control_mode_p_from_t0 --t-ramp 68.61 --t-load 88.61 --t-hand 0 --t-end 388.61
python3 a72_transient.py s_ramp_td2p15_noload --t-ramp 68.61 --t-load 1e6 --t-hand 1e6 --t-end 88.61 --t-dead 2.15 --stall-periods 20
python3 a72_transient.py s_ramp_td0p05_noload --t-ramp 68.61 --t-load 1e6 --t-hand 1e6 --t-end 88.61 --t-dead 0.05 --stall-periods 20
python3 a72_transient.py s_ramp_td2p15_loaded --t-ramp 68.61 --t-load 0 --t-hand 1e6 --t-end 88.61 --t-dead 2.15 --stall-periods 20
python3 a72_transient.py s_ramp_td0p05_loaded --t-ramp 68.61 --t-load 0 --t-hand 1e6 --t-end 88.61 --t-dead 0.05 --stall-periods 20
python3 a72_transient.py main_ramp68p61_stall20 --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61 --stall-periods 20
python3 a72_transient.py main_ramp68p61_fixes --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61 --stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400
python3 a72_transient.py fast_ramp6p861_fixes --t-ramp 6.861 --t-load 26.861 --t-hand 26.861 --t-end 326.861 --stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400
```

Wall time is ~1-1.5 s per simulated us. The datasheet PDFs (UCC28051,
UCC28063A) are not in this repository.
