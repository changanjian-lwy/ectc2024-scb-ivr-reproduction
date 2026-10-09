# A183 - the open-loop start-up period against the series-capacitor ladder split (BOUNDARY)
Method: mixed (cosim: EPC2067 gate model on all eight switches, threshold interlock 1.0 ns, frozen RTL; cfg only:
t0_ns and the per-board trim ton_ns. Math: a volt-second estimate of the mode-S valleys, Section 3)
Track A, package layer, plant V5. Written and committed before the runs. Prompted by the A181 records (below).
Decision it changes: whether the slow corner keeps 200 A at L x 0.75 through a start-up setting (mode-S period +
per-board trim) with the RTL untouched, lifting FINAL_SPEC's "L x 0.75 with nominal devices only"; if not, the fix
has to go into the controller's handover (an RTL decision for the user).
Cheaper check done first: records only (A181 / A173 / A178 start-ups, 7 boards) - below; D63 has no mode S.
Budget: stage 1 12 start-ups (~15 min, --jobs 5); stage 2 ~18 trim start-ups + 5 full + 5 short runs (~3 h).

## 1. What and why
- A181's slow-corner L x 0.75 board (S75) fails 200 A both ways: open-loop start-up 202-211 A at every trim, and
  at the trim near Vo 1.035 V a handover runaway to 278-282 A. The records show one cause upstream of both: in
  mode S (fixed period t0 = 400 ns, fixed 4.5 ns dead time) the per-phase valleys are not regulated; S75's are
  +12.6 / +7.4 / -32.8 / -35.6 A, so phases 1-2 turn on hard (lose on-time on slow gates) and 3-4 with ZVS, and the
  ladder splits: rails 15.6 / 14.8 / 8.9 / 8.7 V (ideal 12 V; max/min 1.80). Nominal L0 1.08, nominal L x 0.75
  1.23, ss L0 1.61 (phase 4 alone at -17 A), nominal L x 1.3 1.02 (all valleys +17 A).
- Handover: mode P drives every valley to -15.6 A; on S75 phases 3-4 collapse (peaks 27 A), Vo falls 74 mV, and
  where Vo(144 us) was only ~35 mV above 1.0 V the loop winds Ton to 1.28-1.31x and phases 1-2 (high rails) reach
  278-282 A; with Vo(144) >= 1.065 V it does not (5 S75 runs, no exception). Track B (R04E5) already required the
  handoff only once Vo and the ladder are near target.
- Method: t0 moves all mode-S valleys to one side (all hard: short t0; all ZVS: long t0). Stage 1 screens t0 on S75;
  stage 2 validates the picked t0* on seven boards, each re-trimmed once at 25 C at t0* (A164 / A181 rule).
- Not tested: other rows than +4.8 V / 1 us; four modules (stage 3, conditional); dead time; RTL changes.

## 2. Criteria
Stage 1 (S75, 25 C, t0 200 / 250 / 300 / 500 ns x 3 trims, start-up to 170 us). Peaks are physical gate turn-off
peaks; start-up = before mode P, handover = mode-P entry .. + 25 us. For each t0 the two runs bracketing Vo(143.5 us)
= 1.035 V (if none bracket: one extra pair by the slope of the nearest two) must both meet:
 S1 start-up <= 200 A;  S2 handover <= 200 A;  S3 V_DS <= 40 V, 0 shoot-throughs / overlaps, COMPLETED.
 t0* = the passing t0 with the lowest max(start-up, handover) over its pair. Diagnostic: ladder max/min, valleys.
Stage 2 (t0*, each board trimmed once at 25 C: three 150 us start-ups, interpolated to Vo 1.035 V; boards S75 ss
L x 0.75, S0 ss L0, N0 nom L0, N75 nom L x 0.75, N07 nom L x 0.7, N13 nom L x 1.3, F0 ff L0). Full runs (+4.8 V /
1 us at 500 us + k T / 3, end + 400 us): S75 25 C k = 0, 1, 2 and S75 125 C k = 0 (trim locked), N0 25 C k = 0.
Short runs to 300 us: S0, N75, N07, N13, F0 at 25 C.
 c1 start-up and handover <= 200 A on every run;  c2 post-step <= 200 A (full runs);
 c3 V_DS <= 40 V, COMPLETED, 0 shoot-throughs / overlaps;  c4 Vo(143.5 us) in 0.99-1.17 V (S75 125 C, locked);
 c5 no harm in mode P: each board's mean per-phase peak over 250-300 us within +-2 A of its t0 = 400 record
    (S75 A181 S75_25_p0; S0 A173 il1p4_ss; N0 A173 nom_s_p62; N75 A178 L075_sh0; N07 A173 il2p0_nom_L07;
    N13 A173 nom_L13; F0 A173 ff_s_p62).
Diagnostic: ladder max/min at entry, Vo min / max after entry, Ton max / cfg, late fires, and the peak between
entry + 25 us and the step (pre_step_pk, covered by neither c1 nor c2; flagged if > 200 A).
Added before stage 2 (criteria unchanged): trim start-ups at a guess and -+ 2 ns (make_cfgs cal: 1.035 V t0* / 12 V +
k x S75's on-time loss at t0*, k 1 slow / 0.42 nominal / 0.30 ff); unbracketed boards get stage 1's extra-pair rule.

## 3. Predictions (not criteria)
Volt-second estimate: mean mode-S valley = I_avg - Vo (t0 - T_eff) / (2 L), T_eff = Vo t0 / 12 V, Vo 1.035 V,
L 2.2 nH, I_avg 74 A (S75's mode-S mean at 400 ns, which this reproduces: -12 A). Split zone: valleys between
the ZVS threshold (~ -24 A, D57) and ~ +5 A.
- t0 200: valleys ~ +31 A, all hard -> ladder <= 1.15, start-up <= 150 A; valley gap at entry ~47 A -> Vo dip and
  Ton 1.1-1.3x, handover 150-200 A (least certain); trim ~33 ns.
- t0 250: ~ +20 A, phase 4 may split -> 1.1-1.4, start-up <= 170 A; trim ~37.5 ns.
- t0 300: ~ +10 A, split -> 1.4-1.8, start-up 180-205 A; trim 38-42 ns.
- t0 500: ~ -34 A, all ZVS -> <= 1.3, start-up 180-200 A (larger ripple), current rises at entry (no dip),
  handover <= start-up; trim 39-43 ns. Expected t0*: 200 or 250.
- Stage 2: c5 holds (t0 acts before mode P's period is known); the risk is N13 / F0 (valleys far positive at a short
  t0: larger entry gap) and the seed: ton_ns also seeds the loop integrator and the 0.5x / 2x clamps.

## 4. Decision rule
- Stage 1 no t0 passes: the cfg route is closed; the fix belongs in the handover (e.g. hand over once the ladder is
  within a set ratio, Track B's rule) - RTL, named with evidence for the user. Stages 2-3 not run.
- Stage 2 passes c1-c5 everywhere: t0* + per-board trim at t0* becomes the start-up spec; FINAL_SPEC: L x 0.75 holds
  at the slow corner too (tested points). Stage 3: four nominal modules at t0* to 300 us (start-up / handover <= 200 A,
  V_DS <= 40 V) before FINAL_SPEC is changed; if it fails, single module only, four modules named open.
- S75 passes but another board fails c1 or c5: no single t0 for all boards - per-board t0 named, not adopted.
- c3 fails anywhere: reported first; t0* not adopted.
