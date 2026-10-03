# ml_design_assist - machine learning that assists the physics models

**An extension, not the reproduction.** Machine learning, deep learning
and reinforcement learning, used where they help. Asked for on
2026-10-03.

## Rules

1. **The physics stays the authority.**
   - D57-D63 and the co-simulation decide.
   - A learned model is a fast or uncertainty-aware stand-in for them,
     checked against them.
2. **numpy and scipy only.**
   - No new dependencies, and CI stays light.
   - Every step (forward and backward pass, Adam, the Gaussian process,
     the policy gradient) is written out to be read.
3. **Every experiment registers its targets before training,** as the
   main line does (BOUNDARY → runs → RESULTS).
4. **Reinforcement learning can exploit model error.**
   - D63's known blind spot is the timed 60 kHz design on fast line
     steps.
   - A learned policy counts only once it is distilled into a rule the
     RTL can implement and checked in the co-simulation.

## Experiments

Numbers are shared with the main line; A118 and A119 are reserved there.

| # | method | what | status |
|---|---|---|---|
| [A120](experiments/A120_d63_surrogate_mlp/RESULTS.md) | deep learning: a multilayer perceptron | a surrogate of D63 (design + disturbance → peak, Vo extreme, phase 1's crossing, recovery), for fast design-space queries | **done:** all targets met (test peak MAE 2.0 A, 11 000× faster, co-simulation error 8.7 against D63's 9.2 A); the search finds the floor rule with Cs ≲ 8 µF feasible once the bus slew is ≥ 5 µs |
| A121 | Gaussian process | the residual co-simulation − D63 with its uncertainty; choosing the next co-simulation runs (active learning) | planned |
| A122 | reinforcement learning (policy gradient) | phase 1's turn-off decided per period in the D63 environment, against the hand rules (comparator, timed, floor) | planned |

## Code

- `src/scb_ivr/extensions/ml_nn.py`: the MLP; tested in
  `tests/extensions/test_ml_nn.py` against finite differences.
- `src/scb_ivr/extensions/ml_d63_data.py`: D63 datasets.
