# Track A: A49-A52, the first SPICE-confirmed four-phase joint ZVS periodic state

## Why this document exists

`A49` through `A52` were produced across one continuous working session
(2026-09-18/19), each individually documented (`BOUNDARY.md`/`RESULTS.md`
per experiment). This document synthesizes the four into one narrative
and states plainly what is and is not established. Read the individual
`BOUNDARY.md`/`RESULTS.md` files for full numerical detail -- this is a
map, not a replacement.

## The headline result, stated precisely

**SPICE independently confirms a self-consistent four-phase joint
periodic state in which all four phases achieve natural zero-voltage
switching (ZVS).** This is the first time, by any method (SPICE search,
symbolic derivation, or the fast solver built for this purpose), that
this project has found a four-phase ZVS periodic state at all -- and it
is now confirmed two ways: a fast, custom Python descriptor-model solver
(`A51`) and independent LTspice physics (`A52`), agreeing on all four
phases' own crossing times to within `0.11%-0.24%`.

**What this is not**: a P24/P25 reproduction, or a claim about the paper's
own rated `250 W` operating point. The state found is at `76%` of rated
load (`~190 W` actual delivered power under realistic device resistance).
At the rated `250 W` point, the same tools find a genuine periodic
fixed point, but ALL FOUR phases hard-switch -- ZVS is not achieved there.
This is `SENSITIVITY_ONLY` throughout, not a paper-value branch.

## The chain, in order

### A49 -- cross-checking the parallel math model's periodic orbit (negative)

A separate, ideal-switch effort in this repository (`src/scb_ivr/`)
independently solved a self-consistent periodic orbit for this topology.
`A49` imported that orbit's own state into `A37`'s real-device SPICE
construct to see whether it would transfer. It performed WORSE than
A37's own arbitrary optimizer-found seed (`1/15` residuals converged vs
A37's `3/15`; `0/4` ZVS admissions vs A37's `1/4`) -- traced to the
seed's own weakest link (a period-average current substituted for an
instantaneous snapshot). This motivated building a tool that could
search the real-device physics directly and fast, rather than importing
an ideal-model guess.

### A50 -- a validated, ZVS-capable fast solver

Rather than keep guessing seeds for slow SPICE, `A50` extended a COPY
(never the original) of the ideal-switch effort's own fast affine-map
solver with real switch capacitance and genuine event-driven dead time --
the two physical ingredients an ideal-switch model structurally cannot
have. Validated on two independent gates before being trusted for
anything new: exact regression at zero capacitance/dead-time (bit-for-bit
reproduction of the original ideal periodic orbit), and reproduction of
`A42`'s own already-SPICE-verified single-phase ZVS threshold bracket
(`7.76%` no-cross, `7.77%` crosses, timing agreement within `1.9%`
against a pre-declared `20%` tolerance). Both passed.

### A51 -- searching for, and finding, a four-phase joint ZVS state

Using A50's own validated solver (seconds per evaluation, not SPICE's
20-100+ minutes), `A51` searched for a genuine four-phase joint periodic
fixed point, seeded from A37's own best SPICE candidate. At P24's rated
`250 W`: a fixed point IS found (first time ever for a genuinely closed
four-phase orbit in this project), but all four phases hard-switch. A
load sweep located the mechanism (a ripple/average-current balance that
flips sign with load) and the boundary (`190-225 W`, phase-dependent).
At `190 W`, a converged state exists at which all four phases achieve
natural ZVS. Extensive robustness checks (dead-time, sub-step,
`Rds(on)`, divider admissibility, local stability of the fixed point)
support the finding, but it rested on a Python solver validated only
against a single-phase SPICE case -- a full four-phase SPICE cross-check
was the explicitly flagged next step, not yet performed.

### A52 -- the SPICE cross-check, and confirmation

Before building SPICE, A51's own headline state (which used an idealized
`1 uOhm` switch resistance) was corrected: re-solved with GS61008T's real
`7 mOhm` (uniform on both sides, matching A51's own model -- not A37/
A42's more detailed asymmetric high-/low-side values) at the same
nominal load target. It still converges with all four phases achieving
ZVS, at `89.9 W` actual delivered power (real conduction loss reduces
delivered power below the nominal target). This corrected state, not
the original idealized one, is what A52 built in SPICE.

The switching sequence itself -- fixed `Ton`, dead-time windows centered
symmetrically on the original commanded edges, each transition gated on
"natural zero-voltage crossing OR commanded timeout, whichever comes
first" -- was piloted in isolation (8 runs covering both branches of the
event logic, two independent OR-encodings, two timesteps) before the
full four-phase netlist was built, and every timing window was derived
programmatically from the solver's own code rather than by hand, to
eliminate transcription risk. The full result: **all four phases cross
naturally in SPICE**, at times matching the Python solver to
`0.107%-0.242%` -- roughly 80-190x inside the pre-declared `20%`
tolerance. Every number in this result was independently re-derived from
the raw LTspice `.log`/`.raw` output before merging (crossing times,
safety margins, fingerprint checks), not taken from the delegated agent's
own summary.

## What this establishes, and what it does not

**Establishes**: the SCB-IVR four-phase topology, with real GS61008T
device capacitance and a plausible (though not yet Mihai-confirmed)
dead-time value, genuinely supports a self-consistent periodic operating
point at which all four phases achieve zero-voltage switching --
CONFIRMED independently by two different numerical methods, at one
specific, reduced-load operating point. This directly answers, for the
first time with a positive result, the question this project's own
`A24-A48` chain spent dozens of experiments trying to resolve at the
rated operating point without success.

**Does not establish**:
- That this holds at P24's own rated `250 W` -- the SAME tools confirm
  it does NOT, at that specific point, under these specific assumptions.
- That the real converter (with EPC2067 or another actual device, real
  dead time from an actual gate driver, nonlinear `Coss(V)`, and
  asymmetric high-/low-side on-resistance) behaves this way -- every one
  of those remains a `SENSITIVITY_ONLY`/engineering-assumption choice,
  not a Mihai-confirmed value (`MINIMUM_INFORMATION_REQUEST.md`'s own
  standing gaps are unchanged by this result).
- Any claim about efficiency, thermal behavior, or hardware losses.

## Recommended next steps (a menu, not a decision)

1. **Locate the exact load boundary more precisely** (between `225 W`
   -- confirmed hard-switching -- and `190 W` -- confirmed ZVS) and, more
   importantly, **characterize what would need to change to push that
   boundary up toward `250 W`** (larger inductance, different `Ton`,
   different dead time) -- this is the direct path toward a rated-load
   ZVS claim, if one exists.
2. **Re-test with the more realistic asymmetric `RHS`/`RLS`** (`7 mOhm`/
   `3.5 mOhm`, matching A37/A42's own population-based convention) rather
   than A51's uniform simplification -- requires a fresh Python re-solve
   first, then its own SPICE cross-check.
3. **Extend A50's solver to nonlinear `Coss(V)`** (A47 already found this
   makes the single-phase threshold WORSE, not better -- test whether
   the same holds for the four-phase joint case).
4. **Take this result to Mihai** as concrete evidence that the topology
   CAN support joint ZVS under specific, now-precisely-quantified
   assumptions, and use it to motivate getting the real answers to
   `MINIMUM_INFORMATION_REQUEST.md`'s own standing questions (actual
   device, actual dead time, actual negative-current reference) --
   this result is a much stronger basis for that ask than anything
   available before this chain.

This ranking is a suggestion, not a decision -- next-step selection
remains the user's call, consistent with this project's standing
practice.
