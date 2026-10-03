# A122 - reinforcement learning of phase 1's turn-off rule in D63's environment (BOUNDARY)

Extension `ml_design_assist`. **Written before any training.**

## 1. What and why

**The question:** is the floor (D63's proposal, A118) the best per-period
choice among the turn-off rules the RTL has? Or does a state-dependent
choice do better?

**Agent:** each phase-1 period, it chooses the timed edge, the
comparator at the target, or the floor (2 A).
- Every rule is implementable. So a learned policy is a small state
  machine over existing rules.
- It sees only what the RTL measures:
  - Vo's error (ADC);
  - Ton's deviation from its steady value and its last change;
  - phase 1's last turn-off current against the target (the crossing
    report).

**Environment:** D63 (`src/scb_ivr/extensions/ml_rl.py`, `Env`) at A118's
f6 design: 1 MHz, 10%, Cs 6 µF, 60 kHz.
- **Episode:** a disturbance, then 150 periods. 30% are ±62.5 A load
  steps; 70% are ±4.8 V steps over 1-20 µs (log-uniform).
- **Reward per period:** −(e_vo² / 10 + max(0, peak − 200 A) / 5 + phase
  1's crossing / 5 + the slots' crossing / 20); −50 and the end if the
  map diverges.

**Algorithm:** REINFORCE (policy gradient), a linear softmax policy.
- Discount 0.98; per-time baseline; entropy bonus 0.01;
- 16 episodes per update, 150 updates, learning rate 0.05, seed 0.

## 2. Registered targets

**Evaluation:**
- 64 held-out disturbances (seed 99);
- A118's set: ±62.5 A; ±4.8 V over 1, 5 and 20 µs.

**Against the fixed rules** (always timed, always comparator, always
floor):
1. **Return:** the learned greedy policy's mean held-out return ≥ the
   best fixed rule's − 5%.
   - **Hypothesis:** the floor is near-optimal among these rules. RL
     either matches it (confirming D63's proposal), or finds a better
     state-dependent choice.
2. **Worst peak:** on the held-out set ≤ the floor's + 5 A.
3. **Distillation (reported):** the policy's choices as a function of the
   observation, and whether a rule with ≤ 2 thresholds reproduces ≥ 90%
   of them.

**If it beats the floor by more than 5%:** the distilled rule is a
candidate for the co-simulation (a later experiment). Learned in D63, it
may exploit D63's error, and it counts only after that check.

## 3. Limits

- D63's blind spots carry over: the timed 60 kHz design on fast steps,
  and the 3 µF handover.
- One design, one seed.
