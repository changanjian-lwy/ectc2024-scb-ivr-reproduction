# A41 result - passive snubber does not rescue the P24 1%-2% local event

## Outcome first

All 28 fixed-boundary cases completed numerically. Every case released the low
side at the selected P24 negative-current boundary, but **none reached the
subsequent natural high-side `Vds=0` event within 50 ns**. The event guard
therefore kept the high side off in all 28 cases.

Within this model, adding a positive passive capacitor cannot make the P24
1%-2% claim work. It monotonically increases the residual high-side `Vds` and
delays the minimum-voltage point. Consequently there is no positive snubber
value to promote into the parameter library from this experiment.

## Correct measurement boundary

The raw run starts at the chained P24 `t2` state, where high-side `Vds` is
initially zero. A full-window minimum would therefore falsely report ZVS. The
analysis starts only after the measured low-side release event. At release,
high-side `Vds` is approximately 11.97 V in every case.

## High-side-only added capacitance

| P24 target | Added C | release (ns) | minimum high-side Vds after release (V) | commutated drop (V) | time of minimum (ns) | ZVS |
|---:|---:|---:|---:|---:|---:|:---:|
| 1% | 0 pF | 1.836 | 9.257 | 2.720 | 4.680 | no |
| 1% | 50 pF | 1.836 | 9.281 | 2.696 | 4.754 | no |
| 1% | 100 pF | 1.836 | 9.303 | 2.673 | 4.827 | no |
| 1% | 250 pF | 1.836 | 9.362 | 2.614 | 5.042 | no |
| 1% | 500 pF | 1.836 | 9.440 | 2.536 | 5.375 | no |
| 1% | 1000 pF | 1.836 | 9.548 | 2.428 | 5.994 | no |
| 1% | 2000 pF | 1.836 | 9.671 | 2.306 | 7.068 | no |
| 2% | 0 pF | 3.682 | 7.996 | 3.976 | 6.166 | no |
| 2% | 50 pF | 3.682 | 8.051 | 3.920 | 6.228 | no |
| 2% | 100 pF | 3.682 | 8.104 | 3.868 | 6.289 | no |
| 2% | 250 pF | 3.682 | 8.242 | 3.730 | 6.468 | no |
| 2% | 500 pF | 3.682 | 8.428 | 3.544 | 6.749 | no |
| 2% | 1000 pF | 3.682 | 8.693 | 3.278 | 7.268 | no |
| 2% | 2000 pF | 3.682 | 9.010 | 2.962 | 8.191 | no |

## Symmetric high-side and low-side added capacitance

| P24 target | Added C per side | minimum high-side Vds after release (V) | time of minimum (ns) | ZVS |
|---:|---:|---:|---:|:---:|
| 1% | 0 pF | 9.257 | 4.680 | no |
| 1% | 50 pF | 9.303 | 4.828 | no |
| 1% | 100 pF | 9.344 | 4.970 | no |
| 1% | 250 pF | 9.440 | 5.376 | no |
| 1% | 500 pF | 9.548 | 5.992 | no |
| 1% | 1000 pF | 9.671 | 7.067 | no |
| 1% | 2000 pF | 9.783 | 8.848 | no |
| 2% | 0 pF | 7.996 | 6.166 | no |
| 2% | 50 pF | 8.104 | 6.289 | no |
| 2% | 100 pF | 8.199 | 6.409 | no |
| 2% | 250 pF | 8.428 | 6.749 | no |
| 2% | 500 pF | 8.693 | 7.269 | no |
| 2% | 1000 pF | 9.009 | 8.191 | no |
| 2% | 2000 pF | 9.320 | 9.757 | no |

The near overlap between `symmetric C` and `high-only 2C` shows that this
local response is mainly governed by the total added commutation capacitance,
not by a beneficial voltage-sharing effect unique to the symmetric placement.

## Interpretation and next action

This directly rejects the proposed direction “increase a passive snubber until
1%-2% reaches ZVS” under A41's explicit device-augmented local model. It agrees
with the A40 analytical direction: more capacitance requires more commutation
charge and time. A snubber could still limit `dv/dt` or overshoot in hardware,
but that is a different objective from creating high-side ZVS with a fixed
small negative current.

The next useful experiment is **not** a wider positive-capacitance sweep.
Instead, keep the zero-snubber baseline and determine the negative-current
threshold required for natural ZVS under this exact local state. Then compare
that threshold against P24's 1%-2%, P25's 5%-10%, and the earlier A39 7.77%
global-branch observation without merging their boundaries. Only after that
should a full four-phase periodic case be rerun at the selected, source-labelled
threshold.

## Limit

This is a local P24 `t2->t3` mechanism screen using P25/external device
capacitance supplements. It does not establish a P24 periodic orbit, full
four-phase handoff, startup, loss, hardware snubber need, or the authors'
unpublished capacitance values.
