# A240 - a typical point of load: a 1 kW accelerator's repeated load steps on one module (BOUNDARY)
Method: mixed (plant + bridge option, cfg-gated; cosim on plant V7).
Track A. Written and committed before the runs. Looked at beforehand: A237's single-event records (references below).
Decision it changes: whether the final controller can be stated for a processor-like load (steps repeated at a finite
slew across the loop's band), or a new controller item opens. Every load step so far was one or two instantaneous
events on top of a 4 mOhm resistor or a constant current.
Cheaper check done first: none that covers it; D63 has no skipping and no periodic load. The output's L/4 and Co
resonate at 86 kHz (L0) / 100 kHz (0.75 L0), next to the loop's 100 kHz crossover, so the sweep straddles both.
Budget: 18 runs of 700 us, two waves at 9 jobs, ~1.5-2 h. Code gate: cosim_regression quick + full PASS with the
option absent, test_cosim_plants bit for bit (CHANGELOG 2026-10-22).

## 1. What and why
- The point of load: P24 Fig. 6 places the IVR under an estimated 97 x 84 mm, 1 kW processor package, 48 V to 1 V.
  Our reproduction carries it on four 250 A modules sharing equally (C12 / C13), so one module sees a quarter.
- The load, per module (sources, with their conditions):
  - a constant current (Smith, Sandler, Bogatin, Signal Integrity Journal: the die's impedance is much higher than
    the PDN's, so to first order it is a current source; A237: the conservative bound against the 4 mOhm resistor);
  - steps between 100 % and 10 % (ADI technical article: a 16-phase PoL for xPU rails tested 40 -> 360 A, a vendor
    demonstration on a board); the slow board between 100 % and 30 %, its tested minimum (coverage, load range);
  - 1250 A/us per module, 5000 A/us for the system (a US patent on AI/ML ASIC regulators: > 1000 A, slew > 5000 A/us;
    no test conditions given). ADI's 800 A/us is slower;
  - 50 % duty at 10, 30, 60, 100, 200 and 1000 kHz. No source gives an accelerator's repetition spectrum; the range
    is ours, chosen to straddle the loop and the output resonance.
- Rows (cfgs from make_cfgs.py, final configuration, one module): N0 and N75 at 25 C (A231's lead), S75 at 125 C (plain
  request). 4 mOhm base to 300 us, then the trapezoid (starting at 250 A) to 600 us, then 250 A to 700 us.
- The steps act at Co: the package and die capacitance that would soften them are not modelled (conservative).
- Not tested: four modules (the slaves do not follow a pause), 85 C, a load with a conductance, line steps meanwhile.

## 2. Criteria (after 300 us unless named)
| # | rows | criterion |
|---|---|---|
| q0 | all | provenance.cosim_sources_modified False |
| q1 | all | whole run: COMPLETED, gate-level peak <= 200 A, V_DS <= 40 V, 0 overlaps, 0 shoot-throughs |
| q2 | all | every excursion above 1.05 V shorter than 25 us (Intel VRD 11.1: at most 50 mV over the set point for 25 us) |
| q3 | all | Vo >= 0.95 V (our bound: VRD 11.1's 50 mV applied below; no source for an undershoot without a load line) |
| q4 | all | peak <= the board's single re-application in A237 + 10 A (N0 161.5, N75 171.1, S75h 152.6 A) |
| q5 | all | Vo within 1 % over the last 20 us (100 us after the train) |

References (A237, instantaneous single events, constant current): release 100 -> 10 %: N0 +49.3 mV, N75 +41.4 mV;
100 -> 30 % S75h +30.3 mV; re-application from 5 % / 30 %: N0 -40.7 mV, N75 -30.2 mV, S75h -24.9 mV.

## 3. Predictions (not criteria)
- 10 kHz behaves as single events: N0 +45..+50 / -30..-38 mV, N75 +38..+42 / -25..-30 mV, S75h +27..+31 / -20..-25 mV.
- The largest Vo swing at 60-100 kHz, at most 1.3 x the 10 kHz one; at 1 MHz within +-15 mV (225 A for 0.5 us on Co).
- Peaks within the single-event references; the worst at 30-100 kHz. Every row passes q1-q5.

## 4. Decision rule
- All pass: the coverage and the scorecard state the accelerator load as covered for one module (with the sources'
  conditions); the option stays available, off by default.
- q1 / q4 miss: a repetition effect exists; traced (frequency, phase, mechanism) before anything else, controller item.
- q2 / q3 miss without q1 / q4: the Vo window at that frequency is stated as a limit, and the mechanism traced.
