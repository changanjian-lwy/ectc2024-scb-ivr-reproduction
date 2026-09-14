# A46 cross-experiment commutation-capacitance scaling boundary

Track: A, post-hoc analysis across three already-completed local P24 `t2->t3`
commutation experiments. This is not a new SPICE experiment; it makes no new
netlist and runs no new LTspice case. It is a joint regression over rows
already produced and committed by A41, A42 and A45.

## Why this file exists

The underlying curve fit was first computed ad hoc in conversation (an
inline Python session, output only to chat and to a `/tmp` scratch file) and
was never saved to the repository. That is a process failure by this
project's own rule that a result is not usable until it is reproducible from
the repository, not from a transcript. This experiment corrects that: the
same analysis, rebuilt as a committed script over committed source data, so
anyone can rerun `fit_cross_experiment_scaling.py` and get the same numbers.

## Parent data (unchanged, no new simulation)

All three source experiments share the same electrical parent
(`R04D3A_P24_interval3_same_phase_ZVS.cir`-derived chain: `Vin=48V`,
`Vo=1V`, `nP=4`, `Ipk=125A`, `L=1.4667nH` Eq.-4 branch) and the same
measurement (`minimum_vds_high_after_release_v`, i.e. the local high-side
`Vds` minimum after low-side release, against a negative-current release
target `negative_target_a`):

- `A41_p24_snubber_local_sensitivity/results.csv` -- fixed 1%/2% negative
  current, added snubber `0-2000 pF` on `CH1` only (`high_only` branch) or
  on both `CH1`/`CL1` (`symmetric` branch), on top of the GS61008T baseline
  (`CH=385 pF`, `CL=770 pF`).
- `A42_zero_snubber_negative_current_threshold/{coarse,refinement}_results.csv`
  -- GS61008T baseline (`CH=385 pF`, `CL=770 pF`), negative current swept.
- `A45_epc2067_table3_candidate_commutation/{coarse,wide_bracket,refinement}_results.csv`
  -- EPC2067 candidate (`CH=3720 pF`, `CL=5580 pF`), negative current swept.

## Only changed variable across the combined dataset

None, in the SPICE sense -- no new circuit is run. The regression's two
independent variables, read directly from the above files, are the release
current magnitude (`negative_target_a`) and the effective series
commutation capacitance `Ceff = CH*CL/(CH+CL)` (computed per source row from
each experiment's own fixed `CH`/`CL`, not re-simulated).

## Model and fit method

`Vds_min = V0 - k * Ineg / Ceff^p`, fit by nonlinear least squares
(`scipy.optimize.curve_fit`) over all 102 combined rows, `p` left free (not
fixed at 0.5). See `fit_cross_experiment_scaling.py`.

## Direction, stated unambiguously

Two different quantities move in opposite directions with `Ceff` and must
not be conflated:

1. At **fixed** `Ineg`, the achieved voltage swing (`V0 - Vds_min`) falls
   off as `Ceff^-p` -- i.e. `Vds_min` moves **up**, away from zero/ZVS, as
   `Ceff` grows.
2. The **negative-current threshold** needed to reach `Vds_min=0` scales as
   `Ineg_threshold = (V0/k) * Ceff^{+p}` -- i.e. it **increases** with
   `Ceff`, not decreases. This is the quantity relevant to comparing A42
   (GS61008T) against A45 (EPC2067).

An earlier informal write-up (draft email) described this only as "Vds_min
falls off as roughly 1/sqrt(Ceff)" without stating which of the two
quantities/directions above it meant. Taken alone, at fixed `Ineg` that
sentence is not wrong, but it is easy to misread as claiming the *threshold*
scales as `1/sqrt(Ceff)` (i.e. decreasing with `Ceff`), which is the wrong
direction. That email must be corrected to state direction (2) explicitly
wherever a threshold comparison is intended.

## Prohibited claims

This is a cross-sensitivity regression over constant-capacitance,
`Ron`-frozen, single-phase local results. It does not establish a validated
P24 hardware threshold, a nonlinear `Coss(V)` model, four-phase periodic
closure, or which device (GS61008T, EPC2067, or neither) the paper's
Sec. II-B mechanism actually uses. The fitted exponent and `R^2` describe
how well a simple constant-capacitance LC-energy model explains these three
experiments' own data; they are not a general physical law independent of
that approximation.
