# A140 - why the post-step peak is not monotone in line-step slew (BOUNDARY)
Track A. Written and committed before the cosim runs. Looked at beforehand: A138 / A139 records and the D63 scans below.
Decision it changes: how the bus line-step spec is written - a minimum slew (if one parameter makes the peak monotone)
or forbidden slew windows - and whether gth 50 goes to the user as a fix.
Cheaper check done first: D63 + RTL-exact scb_vff (`a140_d63.py`, stages s1-s3, ~20 000 runs, 8 step positions each;
the base arm reproduces A138's prior bit for bit). Budget: 36 cosim runs, ~20 min at 10 jobs.

## 1. What and why
- A139 found falling -4.8 V 192.2 A at 2.3 us between 173.5 (1 us) and 172.2 A (5.1 us), and rising +4.8 V at L x 0.7
  205.9 A at 20 us vs 185.2 (1 us). Correction: the 192.2 A run (A138 af032) is L x 0.9, Cs x 1.05, not nominal.
- D63, falling: the bump is the falling-term slope gate. g = lp2 - vin lags a ramp by ~3 samples x dv per sample; with
  gth 100 codes (2 V) the gate never opens on -4.8 V slower than ~2.3 us (-6.4 V ~3.1, -8 V ~4.0 us at L0), but such a
  fall is still fast enough to drive phase 4 to ~186 A without the term. Cap removed: identical curve. gth 50: rise with
  slower slew <= 2.4 A on -4.8 / -6.4 / -8 V at L x 0.7 / 1.0 / 1.3 (base 12-34 A); gth 60 leaves 8.3 A at L x 0.7.
  Cost: slow falls at L x 1.3 open the gate (-8 V / 10 us +9 A); A128 (gate always open) cost +20 A in cosim on
  -8 V / 10 us where D63 showed +4 A, so the cost must be measured in cosim.
- D63, rising: the rise is in the plant + voltage loop (vff off: +11.6 A from 5 to 20 us at L x 0.7, +4.8 V). On a slow
  ramp the flying caps lag (rail 1 12.1 -> 14.9 V, rail 4 stays 12.0 V), recharging them starves Vo and the loop raises
  Ton (27.1 -> 29.2 ns) while rail 1 is high. The low-pass cap clips this, then releases ~7 us after the ramp: its rail
  estimate (vin - 3/4 lp20 - vo) reads ~0.7 V below rail 1. No single vff parameter fixes all rows: sh20 7 / 8 cut the
  +4.8 V rise to 3.8 / 2.6 A but raise +8 V at L x 1.0 / 20 us 199 -> 207 / 222 A; rel 288 / 352 are worse. The rising
  peak falls again for slow ramps (L x 0.7 +8 V: 224 A at 20 us, 191.5 at 50 us).
- Arms (C10 template, single module, step at 1000 us, end 1200 us): B = adopted (gth 100); G = gth 50; O = no vff.
  Runs: `make_cfgs.py` RUNS (26 falling, 10 rising incl. 3 step-position repeats at 1/4-period offsets and one
  identity run); 5 B runs reused from A138 / A139 (REUSED). Gate state is reconstructed from each record's ADC Vin
  samples (sections vin_v) in the RTL's integer arithmetic. Not tested: Cs corners, four modules, load steps.

## 2. Criteria
1. Identity: G_L070_p4.8_s20.0 (rising, gate never opens) is bit-identical to A139 ur01 (every section's vo and ton_lsb).
2. Falling mechanism (B): on the nominal -4.8 V and -6.4 V lines the worst run has the reconstructed gate closed, and
   its peak exceeds the line's fastest gate-open run by >= 10 A.
3. Fix monotone (G): on the nominal -4.8 V line (1.0-5.1 us) and -6.4 V line (2.4-5.7 us) the peak never rises by more
   than 3 A from a faster to a slower slew (A139 falling scatter floor 0.97 A).
4. Fix cost bounded (G): (a) -8 V / 10 us at L x 1.0 and 1.3 and -8 V / 12.1 us at L x 1.3 <= 190 A; (b) on each nominal
   line, G's worst peak at slews >= 2.4 us <= B's worst at the same slews.
5. Rising mechanism: O at L x 0.7, +4.8 V: 20 us >= 5 us + 5 A; B: median of the four 20 us positions >= 5 us + 5 A
   (beyond A139's rising floor 4.1 A).

## 3. Predictions (not criteria) - `a140_predictions.json`
D63, mean over 8 positions (falling D63 error +7.8 +- 19.6 A, A139; rising under-predicted up to 17 A, A135):
B -4.8 V 2.0 / 2.5 / 3.0 / 4.0 us 162 / 185 / 180 / 173 A; G 168-169 A flat; B -6.4 V 3.1 us 201 A, G 181 A;
-8 V / 10 us L x 1.3 B 168, G 177 A; L x 0.7 +4.8 V B 10 / 20 / 40 us 189 / 188 / 176 A, O 5 / 20 us 186 / 197 A;
L x 0.7 +8 V 20 / 50 us 224 / 191.5 A.

## 4. Decision rule
- 1-4 pass: gth 50 goes to the user as the falling fix (adoption is the user's call); the falling spec returns to a
  minimum slew per |dv|; its validation on A124's rows, L corners and four modules is a follow-up experiment.
- 3 or 4 fails: the falling spec is written as forbidden windows (B's gate-closed band per |dv| and L).
- Rising: written as forbidden windows whatever 5 gives (no single parameter in D63); 5 says whether the cause is the
  plant (pass) or scatter (fail). A structural fix (rail estimate from the flying-cap voltage) is out of scope.
