# A127 - PPO with an anchored, pure feed-forward policy (RESULTS)

**Boundary:** d00a4e8; amended before retraining (6efc82d).

**Records:**
- `a127_summary.json`, `a127_baselines.json`, `a127_policy_*.npz`,
  `a127_round1_training.json`;
- `a127_distill_vin_ff_s{1,2}.json`;
- `a127_hybrid.json` (post hoc).

All numbers are D63 at A124's 2.5 MHz design, peaks in A.

## 0. Verdict

1. **The structural fixes work.**
   - **Every vin_ff seed passes** the steady-identity and long-horizon
     checks. A126's policies failed them.
   - **Every vin_fb seed fails,** as predicted. Feeding back the
     controller's own signals re-opens the steady state even with
     anchoring.
   - **The asymmetric critic was necessary** (amendment): round 1 failed
     to train vin_ff at all.
2. **The pure feed-forward beats the physics laws on return:** −14.8 /
   −16.0 / −31.6, against cap_vin's −138.0.
   - **Falling steps:**
     - −4.8 V / 1 µs falls from 206 to 172-180 A, which no fixed law
       touches;
     - the worst held-out peak falls from 275 to 206-221 A.
   - **But it misses criteria 2 and 4:**
     - the best seed (s1) reaches 207 A on +4.8 V / 1 µs (≤ 180
       registered); s2 reaches 182 A;
     - on rising rows its Vo extremes are 5-7 mV worse.
3. **What it learned (distillation).**
   - The rule: 6 parameters, phase groups {1}, {2, 3}, {4} on the
     rectified (Vin − 2 µs low-pass). It keeps 85% (s1) and 91% (s2) of
     the gain and passes the checks.
   - **Falling Vin, the same in both seeds:** Ton moves from phase 4
     (−0.85 / −0.51) and phases 2-3 (−0.29 / −0.20) to phase 1 (+0.39 /
     +0.75). That is the rail-ratio direction: phase 1's rail drops
     first.
   - **Rising Vin:** the seeds disagree (s1 cuts, s2 raises), so that
     part was not learned robustly. The physics cap does better there
     (193 against 205-207 A).
4. **The hybrid** (post hoc; cap_vin for rising + s1's learned falling
   part):
   - return −28.8; checks pass;
   - A124's rows +4.8 V 1 / 5 µs **193 / 177**, −4.8 V 1 µs **170**,
     loads 177 / 144;
   - Vo extremes +10 / +6 / +14 / +18 / +26 / −10 / +17 mV, against
     none's +13 / +7 / +54 / +33 / +34 / −10 / +17;
   - **no row worse than no feed-forward.**

## 1. Criteria (BOUNDARY Section 2)

| # | criterion | result |
|---|---|---|
| 1 | every vin_ff seed passes both checks | **pass** (3/3; vin_fb 0/3) |
| 2 | best valid vin_ff: +4.8 V 1 / 5 µs ≤ 180 | **miss** (s1 207 / 175; s2 182 / 173) |
| 3 | best valid vin_ff return > cap_vin (−138.0) | **pass** (−14.8) |
| 4 | no harm (loads ±3 A; Vo ≤ +3 mV) | **miss** (loads pass; Vo +5 mV on +4.8 V / 1 µs) |

**Predictions:**
- −4.8 V / 1 µs ≤ 195 A: holds (172-180).
- vin_fb has the higher return but fails a check: half holds. It fails
  every check; its return −20..−22 is lower than vin_ff's best.
- Worst held-out > 200 A: holds (206-221).

**Decision (Section 5):** criteria 2 and 4 miss, so **cap_vin goes to
A128**, as registered.
- **The learned falling-step part is added as a registered extension of
  A128,** the hybrid. On rising rows it is identical to cap_vin, because
  the falling term is zero there. So A128 tests cap_vin exactly as
  registered, plus the learned part on falling rows.

## 2. Limits

- D63 only. A125 puts D63's rising-step peaks ~10% low.
- The hybrid was assembled after the registered evaluation. A128's
  co-simulation is its test.
- One design and one load level.
