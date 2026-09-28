# A61 - inductor-loss break-even for the tuned large-ripple advantage (BOUNDARY)

Track: A. Classification: `SENSITIVITY_ONLY` (break-even analysis; no new
solve). Not a P24/P25 reproduction. Part of the user's 2026-09-28
direction to finish all self-doable work before asking the advisor. The
inductor's large-signal model, DCR and losses are item 5 of
`results/MINIMUM_INFORMATION_REQUEST.md`.

## 0. Why this experiment exists

Every A50-A60 solve sets the phase-inductor winding resistance to
`1e-6 Ohm` and has no core model, so all inductor loss is absent. The two
designs carry the same DC current per phase (~62.5 A) but very different AC
current. At the A59 anchors, the AC rms is 87 A for the large-ripple design
and 37 A for the baseline, and the peak is 217 A vs 128 A. Inductor loss
therefore counts against the large-ripple design. No inductor data are
available (the locked paper notes do not describe the inductor technology).
The self-doable step is to compute how much inductor loss the advantage can
absorb, and to turn that into inductor specifications that can be checked
against a real part or asked about.

## 1. Method

`inductor_break_even.py` replays the two regulated periodic orbits (the
tuned large-ripple and baseline points of the reference model, A59). It
extracts each phase current and computes DC, rms, AC rms, peak,
peak-to-peak ripple and the rms of harmonics 1-4 of `f_sw` (DFT of the
one-period orbit). Break-even quantities, each at which the given
advantage `dP` (from A59/A60) is used up:

- winding resistance, same value `R` in all eight inductors:
  `R* = dP / sum_phases(Irms_zvs^2 - Irms_base^2)`;
- winding resistance scaled with inductance, `R_zvs = R_b (L_zvs/L_b)^a`:
  `a = 0.5` models the same structure with fewer turns (`L ~ N^2`,
  `R ~ N`), and `a = 1` models resistance per nH. Result is `R_b*`;
- AC resistance at 5 MHz, same value in all inductors, from the
  fundamental-harmonic rms: `R1*`;
- extra core loss: the four large-ripple inductors may lose at most `dP`
  more than the baseline's. Also reported: the flux-linkage swing ratio
  `L*dI_pp` (volt-second ratio) and the peak-current ratio, which set
  saturation margin.

These are post-processing identities on the orbits. The orbits are not
re-solved with the added resistance; a winding resistance of ~0.1 mOhm
changes the regulated operating point by <0.1%.

## 2. Provenance

| Value | Source | Category |
|---|---|---|
| Orbits, advantage | A59 (and A60 for other Tj) | inherited |
| Equal/scaled resistance assumptions | This document | `PROJECT_DECISION` |

## 3. What the result can and cannot decide

Decides: the inductor DCR/ACR and extra core loss above which the
large-ripple design stops paying, stated in numbers that can be checked
against any candidate inductor.

Cannot decide: the actual inductor, its loss, saturation or `L(I)`, or
paper reproduction.

## 4. Constraints

Read-only use of A59/A60 records. Do not modify `src/scb_ivr/`,
`results/`, `paper_locked/`, or any A37-A60 file.
