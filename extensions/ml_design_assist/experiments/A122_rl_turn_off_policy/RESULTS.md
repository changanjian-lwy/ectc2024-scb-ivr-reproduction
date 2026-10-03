# A122 - reinforcement learning of phase 1's turn-off rule in D63's environment (RESULTS)

Extension `ml_design_assist`.

**Boundary:** `BOUNDARY.md`, committed (bb39ea5) before training.

**Records:**
- `a122_policy.npz` (the weights and the training curve);
- `a122_summary.json` (`run_a122.py`; 150 REINFORCE updates of 16
  episodes, 20 s).

## 0. Verdict

1. **Reinforcement learning rediscovers the floor.** Every registered
   target is met.

   | policy (held-out, 64 disturbances) | mean return | worst peak | peak ≤ 200 A | phase 1's largest crossing |
   |---|---|---|---|---|
   | always timed | −54.5 | 214 A | 84% | 88.8 A |
   | always comparator | −152.8 | 307 A | 52% | 2.7 A |
   | always floor | **−30.5** | 214 A | 81% | 4.7 A |
   | **learned (greedy)** | **−30.5** | 214 A | 81% | 4.7 A |

   - **On A118's 8 disturbances** the learned policy's return and peak are
     identical to the floor's, disturbance by disturbance.
   - **Its choices:** floor 64%, timed 33%, comparator 0.3%.
   - **Distilled:** one threshold reproduces 95.9% of them: "phase 1's
     last turn-off current ≤ the target + 0.8 A → floor, else timed".
   - **This is the floor in disguise.** When the last turn-off was above
     the target, the timed edge comes before the floor can act, so the
     two choices behave the same. The policy's choice there is a tie,
     not a different rule.
2. **Within the rules the RTL has, the floor is (D63-)optimal.** A
   state-dependent choice found nothing better. There is nothing new for
   the co-simulation; A118 tests the floor itself.
3. **What the trade-off map gains:** an independent search, by a method
   that knows nothing about D63's reasoning, lands on the same rule. That
   is evidence for T13's resolution in the model, not proof in the
   converter.

## 1. Limits

- **D63's environment:** D63's blind spots carry over (the timed 60 kHz
  design on fast rising steps, the 3 µF handover). The floor behaves as
  the timed design on rising steps, so the co-simulation (A118) is the
  check.
- **A linear policy over 3 existing rules:** a richer action (a dlo
  offset, a floor depth per period) is not explored.
- One design (Cs 6 µF, 10%, 60 kHz), one seed.
