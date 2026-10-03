# A126 - deep reinforcement learning (PPO) of a per-phase Ton feed-forward for line steps (BOUNDARY)

Extension `ml_design_assist`. **Written and committed before any
training.**
- The fixed laws' numbers (Section 3) were computed first, to set the
  criteria.
- A 3-iteration smoke test checked the pipeline. Its returns were not
  read.

## 1. What and why

**The open problem:** fast rising line steps. It is the only hard
constraint every frequency misses.
- A124 at 2.5 MHz, +4.8 V over 5 µs: 210 A in the co-simulation.
- Phase 1's rail jumps from 12.3 to 16.4 V, because the series capacitors
  cannot follow Vin.
- Phases 2-4 stay ≤ 161 A.

**What D63 shows before any learning** (exploration, 2.5 MHz):

1. **A phase-1 Ton cap from its rail works on the 5 µs step** (187 → 177
   A). On the 1 µs step it stalls at ~193 A.
2. **Equalising the phases' peaks** (Ton_k ∝ 1 / (V_rail,k − Vo))
   **diverges.**
   - The ladder balances itself only because phase 1 takes more charge
     when its rail is high (Cs dV_1 = Q_on,1 − Q_on,2).
   - So limiting the peak and rebalancing compete.
3. **A cap below the +62.5 A load step's 177 A diverges** (165 A).
4. **The fast falling step's peak** is phase 4 (D63 208 A, co-simulation
   216 A). It comes from a positive valley, so no Ton cap on its rail
   touches it.

**The problem is therefore multi-input and constrained:**
- four Ton's;
- peaks ≤ the limit;
- Vo regulated;
- the ladder still rebalancing.

The fixed laws react to the rail only. A policy that sees Vin's slope
could anticipate. This is what reinforcement learning is for.

**The method: PPO** (Schulman et al. 2017), `src/scb_ivr/extensions/ml_ppo.py`.
- An actor-critic: MLP 64-64 tanh, a Gaussian policy with a learned
  standard deviation, GAE (γ 0.99, λ 0.95), clip 0.2, Adam 3e-4.
- **Written in numpy and tested:**
  - the policy gradient against finite differences of the clipped
    surrogate;
  - learning a stabilising feedback on a scalar system.
- **Environment** (`src/scb_ivr/extensions/ml_rl_ff.py`):
  - D63 at A124's design; one step is one phase-1 period.
  - **Action:** a scale on each phase's Ton, 0.5-1.25.
  - **Reward:**
    - Vo error²;
    - the peak above **I_LIM = 178 A**, which is 200 A / 1.125, A125's
      80% band on D63's rising-step peaks;
    - the ladder's imbalance;
    - the action's size;
    - −200 on divergence.
  - **Domain randomisation:**
    - Cs × 0.8-1.2;
    - line steps +2 to +6 V and −2 to −9 V over 0.5-20 µs;
    - load steps ±20-62.5 A, or none;
    - 120 periods (~60 µs).
- **Training:** 600 iterations × 32 episodes; 3 seeds per sensor set.

**Three sensor sets: the value of a sensor, measured.**
- **rtl:** the controller's own signals only: Vo's ADC, Ton, phase 1's
  turn-off report.
- **vin:** plus an input-voltage sensor (Vin, its change per period,
  Vin minus three low-passes). A hardware addition: **DEVIATION**, P24
  has no Vin sensing. Hence this extension.
- **rails:** plus the series capacitors' voltages (an upper bound).

**Evaluation:**
- **Held-out:** 64 disturbances (seed 12345) and A124's seven step rows
  at Cs × 1.
- **Policies are run greedy** (the mean action). The fixed laws are
  scored on the same disturbances.

## 2. Criteria

1. **Learning beats the physics law with the same sensor.** Each "vin"
   policy's held-out mean return exceeds cap_vin's (−103.4).
2. **The rising rows in D63:** the best "vin" policy (by held-out
   return) brings A124's +4.8 V / 1 µs and / 5 µs peaks to **≤ 180 A**
   (cap_vin: 193 / 177).
3. **The value of information:**
   - **rtl:** the +4.8 V / 1 µs peak stays ≥ 195 A for every seed.
     Without Vin it cannot anticipate.
   - **rails:** the best seed's return is ≥ the best "vin" seed's −5%.
4. **No harm,** for the best "vin" policy:
   - no divergence on the held-out set;
   - A124's load rows: peaks within ±3 A of no feed-forward;
   - Vo extremes on A124's rows no more than 3 mV worse than no
     feed-forward.

## 3. Reference numbers (fixed laws, computed before registration)

| law | held-out return | worst peak | A124 rows: +4.8 V 1 / 5 µs, −4.8 V 1 µs |
|---|---|---|---|
| none | −113.4 | 275 A | 213 / 187 / 206 |
| cap_vin (Vin, τ 20 µs) | −103.4 | 275 A | 193 / 177 / 206 |
| cap_rails (oracle) | −105.5 | 275 A | 194 / 183 / 206 |

## 4. Predictions (not criteria)

- **The fast falling step** (−4.8 V / 1 µs, phase 4): the "vin" policy
  brings it to ≤ 195 A. About a 50/50 call. It needs phases 2-4's Ton
  cut on a falling Vin, which no fixed law here does.
- **The worst held-out peak** (275 A, a −9 V step over ~0.5 µs): stays
  > 200 A for every policy. Too fast for any Ton action.
- **Distillation:** a rule with ≤ 6 parameters, linear in the Vin
  features per phase, keeps ≥ 80% of the best "vin" policy's
  improvement over no feed-forward. Fitted after training.

## 5. Decision rule

- **If criteria 1, 2 and 4 hold:** A127 implements the distilled rule in
  the RTL. It becomes an opt-in Vin input and per-phase Ton scale,
  bit-identical when off. A127 co-simulates A124's rows, registered with
  A125's conformal bands.
- **Otherwise:** the fixed cap_vin law goes to A127 instead.
- **The co-simulation decides, not D63.**
