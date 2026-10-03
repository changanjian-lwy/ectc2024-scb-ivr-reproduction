# A127 - PPO with an anchored, pure feed-forward policy (BOUNDARY)

Extension `ml_design_assist`. **Written and committed before training.**
The fixed laws' numbers (Section 3) were computed first.

## 1. What and why

**A126's policies gamed the reward.** They moved the steady state, so Vo
oscillated and the ladder sat off balance (A126 RESULTS). A127 removes
that freedom by construction.

**Changes from A126:**
- **An anchored residual policy** (`ml_ppo.GaussianPolicy(anchor=...)`):
  - μ(o) = net(o) − net(o with the transient features zeroed);
  - the action is exactly zero in any steady state, at any Vin;
  - the gradient is tested against finite differences.
- **"vin_ff", a pure feed-forward:**
  - inputs: only Vin, its change per period, Vin minus three low-passes,
    and a constant;
  - it cannot form a new feedback loop.
- **"vin_fb":** the same plus the controller's signals (Vo error, Ton,
  phase 1's report), for comparison.
- **Horizon 240 periods** (~120 µs).
- **Reward v2:** Vo e²/4; the ladder 0.05; action changes 2·Σ(Δscale)²
  (`ml_rl_ff`).
- **Unchanged:** 3 seeds × 600 iterations; the same held-out set (64
  disturbances and A124's 7 rows); I_LIM 178 A.

**Checks** (`run_a127.py`), against no feed-forward:
- **Steady identity:** 600 periods without a disturbance at every Cs
  factor. On the last 300: Vo peak-to-peak +0.5 mV, ladder ≤ 0.1 V,
  peak ±1 A.
- **Long horizon:** A124's 7 rows over 1200 periods. On the last 200:
  Vo peak-to-peak +0.5 mV, ladder ≤ 0.2 V, peak ±2 A.

## 2. Criteria

1. **Every vin_ff seed passes both checks.** vin_fb seeds are reported,
   and go forward only if they pass.
2. **The best valid vin_ff** (by held-out return) brings A124's +4.8 V /
   1 µs and / 5 µs peaks to **≤ 180 A** in D63.
3. **It beats the physics law with the same sensor:** held-out return
   > cap_vin's (−138.0).
4. **No harm:**
   - load rows within ±3 A of no feed-forward;
   - Vo extremes on A124's rows no more than 3 mV worse in magnitude.

## 3. Reference (fixed laws, reward v2, horizon 240; all pass the checks)

| law | return | +4.8 V 1 / 5 µs | −4.8 V 1 µs | worst held-out |
|---|---|---|---|---|
| none | −148.0 | 213 / 187 | 206 | 275 |
| cap_vin | −138.0 | 193 / 177 | 206 | 275 |
| cap_rails | −140.0 | 194 / 183 | 206 | 275 |

## 4. Predictions (not criteria)

- **−4.8 V / 1 µs** (phase 4) ≤ 195 A with vin_ff: about a 50/50 call.
- **vin_fb:** a higher return than vin_ff, but at least one seed fails a
  check.
- **The worst held-out peak** stays > 200 A (−9 V over ~0.5 µs).

## 5. Decision rule

- **If criteria 1-4 hold,** distil the best valid vin_ff policy into a
  rule:
  - ≤ 6 parameters;
  - linear in the Vin features, per phase group;
  - keeping ≥ 80% of the policy's return gain over none;
  - passing the checks and criterion 4.
- **That rule goes to A128:** the RTL (an opt-in Vin input and a
  per-phase Ton scale, bit-identical when off) and the co-simulation of
  A124's rows, registered with A125's bands.
- **Otherwise,** cap_vin goes to A128.

## 6. Amendment (before retraining; no policy had been evaluated)

**Round 1 failed to train vin_ff.** Its return fell from −364..−542 to
−2895..−3683 over 600 iterations, and the exploration sd grew to
0.5-0.64. vin_fb trained normally (−33..−38). See
`a127_round1_training.json`; the round-1 policies were discarded
unevaluated.

**Cause:** the critic saw only the actor's observations. For vin_ff those
are Vin features alone, so it cannot attribute penalties to the
converter's state. The advantages are noise, and the sd drifts up, which
destabilises the episodes.

**Fix:**
- **An asymmetric actor-critic** (Pinto et al. 2018):
  - the critic sees the simulator's full state (`Env.critic_obs`: the
    "rails" set plus phases 2-4's valleys, 17 inputs);
  - the actor is unchanged (vin_ff: Vin only);
  - the critic is used in training only, so it puts nothing into the RTL.
- **The exploration sd is capped** at e^−1 (log_std ≤ −1).
- **Both sensor sets are retrained** this way.

**Criteria, checks and the decision rule are unchanged.**
