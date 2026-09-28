# A64 - SPICE cross-check of the A59 tuned comparison with EPC's EPC2067 vendor model (RESULTS)

Track A, `SENSITIVITY_ONLY`. Boundary: `BOUNDARY.md` (commit `9e2e93e`),
unmodified. LTspice 26.0.2 (macOS, Wine). Records: `runs/*.json` (one per
solved point, never overwritten), `results.json` (`build_a64_results.py`),
`logs/*.txt`, phase-1 edge waveforms in `waveforms/`. The EPC library is
fetched by `fetch_epc2067_model.py` into the git-ignored `vendor/` and is not
in this repository.

## 0. Verdict

**With EPC's own EPC2067 model and a declared 5 V gate drive, the tuned
large-ripple design does not beat the tuned baseline at 250 W. The sign of
A59's result reverses:**

| 250 W, Tj 60 C, each design at its own SPICE-tuned timing | R_drv 1.0 Ohm (primary) | R_drv 0.3 Ohm |
|---|---:|---:|
| large-ripple 0.627 nH: P_loss = P_in - P_out | **61.09 W** | **36.95 W** |
| baseline 1.467 nH: P_loss | **43.74 W** | **35.75 W** |
| **large-ripple minus baseline** | **+17.35 W** | **+1.20 W** |
| same, device loss only (passive R removed) | +17.27 W | +1.18 W |
| same, including gate-drive energy | +17.32 W | +1.15 W |
| A59 (ideal switch, datasheet Coss(V), P_B) | -4.58 W | -4.58 W |
| change vs A59 | +21.86 W | +5.76 W |

- **The cause is turn-off V*I overlap, which A59 does not have.** A59's ideal
  switch turns off instantly and the inductor current charges Coss without
  loss. In the vendor model the gate discharges through R_drv + rg
  (0.3 Ohm internal) into Ciss ~2.2 nF, so the channel is still conducting
  while Vds rises. The large-ripple high side turns off at ~189 A per switch
  (the phase current peaks at 217.7 A a few ns later); the baseline high side
  at ~111 A. Turn-off overlap loss is 26.9 W vs 7.7 W at 1 Ohm and 5.9 W vs
  1.05 W at 0.3 Ohm (Section 3).
- **Where the two models should agree, they do.** The vendor model's full-gate
  on-resistance at 60 C is 1.51-1.61 mOhm per device, against A59's
  1.55 mOhm. The model reproduces the datasheet's Coss, Qoss and Ciss typicals
  to within 0.6%. Its hard turn-on loss in the baseline (19.7 W) matches A59's
  capacitive hard-switch loss (~18.9 W) to within ~0.8 W. The conduction loss
  from the vendor currents at 1.55 mOhm/device is 28.3 W (large-ripple) vs
  A59's 28.2 W (Section 4).
- A stronger driver shrinks the effect but does not remove it. At 0.3 Ohm the
  large-ripple design still loses by 1.2 W. Of that, 4.8 W is extra turn-off
  overlap and ~1.8 W is extra conduction at partial gate enhancement, against
  A59's 4.6 W advantage.
- **A59's tuned timing, taken literally as LTspice gate commands, is
  shoot-through.** The vendor channel turns off 3.8-5.3 ns after its command
  (R_drv 1 Ohm), much longer than A59's 0.65-2.15 ns dead times. The channel
  dead times go negative (-1.6/-2.4 ns and -0.1/-2.0 ns) and the losses are
  163.8 W and 114.1 W. The ±0.3 ns sweep therefore cannot be centred on the
  A59 command values. It was centred on the channel-referenced equivalent;
  see Section 7, deviation 1.

## 1. Loss grids (P_loss = P_in - P_out - dE_stored/T, W, 50 ps max step)

Primary case: R_drv 1.0 Ohm, 60 C. `c` = channel-matched centre. Bold =
optimum. `x` = declared outward extension.

Large-ripple, d_fall line at d_rise 3.55 ns (centre d_fall 3.00):

| d_fall (ns) | 2.40x | 2.50x | 2.60x | 2.70 | 2.80 | 2.90 | 3.00c | 3.10 | 3.20 | 3.30 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P_loss | 61.54 | 61.78 | 62.16 | 62.61 | 63.09 | 63.66 | 64.18 | 64.79 | 65.48 | 66.09 |

The d_rise line was run at d_fall 2.40: 3.25 → 62.74, 3.35 → 62.13,
3.45 → 61.80, 3.55 → 61.54, 3.65 → 61.29, 3.75 → 61.20, 3.85 → 61.20.

A second-pass d_fall line at d_rise 3.75 gave: 2.20 → 61.20,
**2.30 → 61.09**, 2.40 → 61.20. That makes the optimum interior.

Baseline, d_fall line at d_rise 4.35 ns (centre d_fall 3.45):

| d_fall (ns) | 2.85x | 2.95x | 3.05x | 3.15 | 3.25 | 3.35 | 3.45c | 3.55 | 3.65 | 3.75 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P_loss | 43.78 | 43.75 | 43.82 | 43.98 | 44.19 | 44.35 | 44.57 | 44.77 | 45.10 | 45.43 |

The d_rise line was run at d_fall 2.95: 3.95x → 43.83, **4.05 → 43.74**,
4.15 → 43.75, 4.25 → 43.84, 4.35 → 43.75, 4.45 → 43.83, 4.55 → 43.84,
4.65 → 43.86. d_rise is flat to within 0.12 W.

The second-pass point (4.05, 2.85) never reached a period-1 orbit
(Section 5). Its range of 43.39-43.73 W does not threaten the ranking.

R_drv 0.3 Ohm, 60 C, full sweep:

- **Large-ripple**, centre (2.70, 1.75).
  - d_fall at d_rise 2.70: 1.25x → 37.04, 1.35x → 37.01, 1.45 → 37.16,
    1.55 → 37.60, 1.65 → 38.03, 1.75c → 38.55, 1.85 → 39.10, 1.95 → 39.75,
    2.05 → 40.51.
  - d_rise at d_fall 1.35: 2.40 → 37.22, 2.50 → 37.09, 2.60 → 37.04,
    2.70 → 37.01, **2.80 → 36.95**, 2.90 → 37.03, 3.00 → 37.10.
- **Baseline**, centre (3.15, 2.00).
  - d_fall at d_rise 3.15: 1.70 → 35.85, 1.80 → 35.79, 1.90 → 35.79,
    2.00c → 35.95, 2.10 → 36.07, 2.20 → 36.39, 2.30 → 36.62.
  - d_rise at d_fall 1.80: 2.85 → 35.76, 2.95 → 35.76, **3.05 → 35.75**,
    3.15 → 35.79, 3.25 → 35.75, 3.35 → 35.80, 3.45 → 35.82.

Point-to-point noise on flat lines is ~0.05 W (tail estimates, Section 5).
That is irrelevant next to the 17 W and 1.2 W gaps.

Every accepted point regulates to |P_out/250 - 1| < 1e-3. The peak phase
current is 217-219 A for the large-ripple design and 127-128 A for the
baseline, the same as A59's 217.1 A and 128.3 A.

## 2. Gate drive and command-vs-channel timing

Gate-drive energy (delivered by the 20 floating sources, measured) is almost
identical in all cases: 8.29-8.35 W per module. That is 81-84 nJ per device
per cycle, consistent with the model's Qg(0→5 V) = 15.1 nC × 5 V = 76 nJ plus
Miller charge. It does not separate the designs (difference ≤ 0.06 W).

Channel instant = the device's internal Vgs crossing the model's knee
k2(60 C) = 2.056 V.

| optimum | edge | command dead time | channel dead time (ph 1-3 / ph 4) | turn-off / turn-on delay | Vds of incoming switch at its channel-on |
|---|---|---:|---:|---:|---|
| large-ripple R1.0 (3.75/2.30) | rise (high on) | 3.75 | 2.23 / 2.07 | 4.27 / 2.72 | -0.34 V (ZVS, 4/4) |
| | fall (low on) | 2.30 | 0.17 / 0.16 | 4.90 / 2.77 | -0.62 V (ZVS, 0.4-0.5 ns reverse) |
| baseline R1.0 (4.05/2.95) | rise | 4.05 | 1.88 / 1.88 | 3.84 / 1.67 | 12.0-12.2 V (hard) |
| | fall | 2.95 | 0.79 / 0.62 | 4.91 / 2.71 | -0.43 V (ZVS, 0.25-0.4 ns reverse) |
| large-ripple R0.3 (2.80/1.35) | rise | 2.80 | 2.06 / 2.02 | 1.92 / 1.17 | -0.04 to -0.38 V |
| | fall | 1.35 | 0.37 / 0.29 | 2.30 / 1.30 | -0.65 V |
| baseline R0.3 (3.05/1.80) | rise | 3.05 | 2.05 / 2.05 | 1.80 / 0.80 | 12.2-12.4 V (hard) |
| | fall | 1.80 | 1.02 / 0.95 | 2.06 / 1.26 | -0.31 to -0.45 V |
| A59 timing, literal, R1.0 large-ripple | rise / fall | 1.95 / 0.65 | **-1.63 / -2.39** | 5.26 / 1.68, 4.73 / 1.69 | 11-12 V (shoot-through) |
| A59 timing, literal, R1.0 baseline | rise / fall | 2.15 / 1.15 | **-0.11 / -2.05** | 3.95 / 1.67, 4.88 / 1.68 | 11-12 V (shoot-through) |

The vendor optimum wants much shorter channel fall dead times than A59
(0.17-0.35 ns large-ripple, 0.75-1.0 ns baseline, vs 0.65/1.15 ns): with a
finite gate the outgoing channel is already weak before the knee crossing.
The ZVS pattern of A59 survives. The large-ripple design reaches zero voltage
on all eight edges. The baseline hard-switches the high side at 12 V on all
four phases.

## 3. Loss decomposition (vendor model, last period, W)

Method (`a64_analysis.decompose_states`, PROJECT_DECISION). Each switch
group's terminal energy is integrated over one period: Vds·Id, with Vds the
branch voltage and Id the metered group drain current. Every instant is put
in one class according to the representative device's internal Vgs:

- **conduction**: Vgs ≥ 4.5 V (channel fully enhanced).
- **turn_on_*** / **turn_off_***: k2 - 3·k3 (1.79 V) ≤ Vgs < 4.5 V, with
  the gate commanded on / off. Each is split into:
  - **_overlap**: |Vds| > 1 V, V·I overlap;
  - **_underdriven**: |Vds| ≤ 1 V, conducting at partial enhancement.
- **third_quadrant**: Vds < -0.5 V with Vgs < k2 (reverse conduction, channel off).
- **off_state**: Vgs < 1.79 V otherwise (channel off).

The classes sum exactly to the group's terminal energy. Terminal Vds·Id
still contains each device's own Coss charge/discharge, which is reactive.
It is removed by subtracting n·Vds·Coss(Vds)·dVds/dt, using the vendor
Coss(V) measured by a 0.1 A charge ramp. This leaves the totals unchanged
and gives the **dissipative** split below.

Without the correction, `off_state` is **negative** for the large-ripple
design (-9.3 W at R1.0). During a ZVS transition the incoming device's Coss
discharges into the inductor current while its channel is still off. The
device *returns* the energy its Coss stored during its previous turn-off, and
that storage is counted inside turn_off_overlap. For the hard-switched
baseline, `off_state` is positive (+1.0 / +4.4 W), because the off device's
Coss is charged by the incoming switch. With the correction every
`off_state` is 0.2-0.3 W, which is the residual of the Coss table and leakage.

| (dissipative, W) | large-ripple R1.0 | baseline R1.0 | large-ripple R0.3 | baseline R0.3 |
|---|---:|---:|---:|---:|
| conduction (Vgs ≥ 4.5 V) | 22.65 | 11.48 | 25.23 | 12.58 |
| turn-on underdriven + turn-off underdriven | 5.89 + 3.59 | 2.35 + 1.47 | 2.87 + 1.84 | 1.10 + 0.74 |
| **turn-on overlap** (hard turn-on incl. Coss dump) | 0.16 | **19.68** | 0.02 | **19.65** |
| **turn-off overlap** | **26.86** (high side 24.92) | 7.70 | **5.86** (high 5.70) | 1.05 |
| third quadrant | 1.15 | 0.40 | 0.47 | 0.04 |
| off-state residual | 0.33 | 0.31 | 0.22 | 0.21 |
| **sum = device loss** | 60.61 | 43.40 | 36.52 | 35.37 |
| passive resistive (R_src, inductor Rser) | 0.47 | 0.40 | 0.40 | 0.38 |
| gate drive (separate source) | 8.29 | 8.32 | 8.30 | 8.35 |

Checks:

- The per-group Vds·Id sum plus passive loss equals the source-side P_loss
  to within 0.03-0.07 W at the optima (the difference is the Coss energy
  change between samples, plus divider leakage).
- The decompositions are fresh 3-period re-runs from the accepted states.
  They reproduce the accepted P_loss to within 0.01 W.

**Large-ripple minus baseline, R1.0:**

- conduction-like: +16.8 W
- turn-on: -19.5 W
- turn-off: +19.2 W
- third quadrant: +0.75 W
- total: **+17.2 W**

In A59 the same comparison is:

- conduction: +9.2 W
- capacitive: -14.0 W
- reverse: +0.1 W
- turn-off: 0
- total: -4.6 W

The turn-off term alone accounts for ~19 W of the ~22 W swing. The rest is
conduction at partial enhancement (Section 4).

Edge energies (phase-1 waveforms, `waveforms/`, R1.0):

- **Large-ripple high side.** Commanded off at 153.5 A. The current keeps
  rising at ~17 A/ns through the 4.9 ns turn-off delay: it is 189 A when Vds
  starts rising and peaks at 217.7 A.
- **Baseline high side.** Commanded off at 96 A; 111 A at the rise; 127.3 A
  peak.
- **Rise time.** On both, the outgoing Vds goes from 0.5 V to 90% in ~2.1 ns.

**R_drv dependence at each case's tuned timing.** Going from 1.0 to 0.3 Ohm:

- **Large-ripple:** loses 24.1 W (60.61 → 36.52). Turn-off overlap goes
  26.86 → 5.86; conduction-like goes 32.13 → 29.94.
- **Baseline:** loses 8.0 W (43.40 → 35.37). Turn-off overlap goes
  7.70 → 1.05. The hard turn-on is unchanged (19.68 → 19.65), because it is
  set by Coss, not by the gate.

The large-ripple result is therefore dominated by gate discharge speed at
~190 A turn-off.

## 4. Where the two models should agree: mapping onto A59's terms

A59's terms are defined in `A59_nonlinear_coss_epc2067/RESULTS.md`:

- `channel`: Ron·I² metered on ideal-switch ON intervals;
- `missed capacitive`: hard/partial turn-on energy not caught by that meter;
- `reverse`: third-quadrant time priced from Fig. 8;
- no turn-off term.

Per the coordinator's reading of A59, the baseline's 18.94 W `channel` also
holds ~25% of its hard-switch capacitive energy (the coarse meter catches
it). Its pure conduction is therefore ~14.2 W, and its total hard-switch
energy is ~18.9 W. This split is approximate and labelled as such.

| term | A59 large-ripple | vendor large-ripple R1.0 | A59 baseline | vendor baseline R1.0 |
|---|---:|---:|---:|---:|
| conduction (A59 channel; vendor conduction + underdriven) | 28.17 | 32.13 | ≈14.2 (of 18.94) | 15.30 |
| vendor currents × 1.55 mOhm/device over the vendor channel-on time | - | **28.33** | - | **13.77** |
| same, over the commanded ON windows | - | 26.24 | - | 13.12 |
| hard/partial turn-on (A59 missed C + in-channel part; vendor turn-on overlap) | 0.19 | 0.16 | ≈18.9 (14.14 + ≈4.7) | 19.68 |
| third quadrant (A59 Fig. 8 price; vendor third_quadrant) | 0.32 | 1.15 | 0.19 | 0.40 |
| turn-off overlap | 0 (not modelled) | 26.86 | 0 | 7.70 |

- **Conduction agrees where it should.** A59's 1.55 mOhm/device applied to
  the vendor model's own currents gives 28.33 W, against A59's 28.17 W for
  the large-ripple design. The baseline gives 13.77 W against A59's
  ≈14.2 W. The currents and duty are A59's; the peak currents match to 1 A.
- **The vendor conduction-like term is higher.** It is +3.8 W (large-ripple)
  and +1.5 W (baseline). The difference is conduction at partial
  enhancement while the gate is still rising or falling: 9.5 W vs 3.8 W in
  the underdriven classes. Most of it is the large-ripple low side, whose
  gate rises for ~3 ns while it carries ~150 A. A small current-dependent
  Rds rise adds to it.
- **Vendor Rds(on) at 60 C vs 1.55 mOhm/device.**
  - **Static single-device DC sweep** (`runs/static_epc2067_vendor_model.json`):
    1.505 / 1.516 / 1.536 / 1.558 / 1.582 mOhm at 10 / 25 / 50 / 75 / 100 A.
  - **In-circuit full-gate ratio** ∫Vds·Id / ∫Id² per device, from each
    group's conduction class:
    - low side: 1.52-1.54 mOhm;
    - high side: 1.58-1.61 mOhm at 1 Ohm (~95-108 A per device) and
      1.535-1.558 mOhm at 0.3 Ohm.
  - **At 25 C:** 1.263-1.323 mOhm (datasheet typ 1.3 mOhm).
  - This confirms A60's reading that 1.55 mOhm ≈ the typical device at
    Tj ≈ 60 C. The model setup is validated there. The deviation is ≤ 4%,
    set by the model's current-dependent channel term.
- **Hard turn-on agrees.** The baseline's hard turn-on is 19.7 W in the
  vendor model and ≈18.9 W in A59: the Coss dump dominates, with ≤ ~0.8 W of
  V·I overlap beyond it. The near-ZVS large-ripple turn-on is 0.16 W vs
  0.19 W.
- **Datasheet check of the model** (`runs/model_check.json`,
  `runs/static_epc2067_coss.json`), vendor model vs datasheet typical:
  - Coss(20 V): 1071-1073 pF vs 1071;
  - Qoss(20 V): 37.22 nC vs 37;
  - Co(tr) 0-20 V: 1861 pF vs 1860;
  - Ciss(Vds 20 V): 2182 pF vs 2178;
  - Q(12 V): 26.44 nC and E(12 V): 151 nJ, vs A59's Fig. 6 values 26.9 nC
    and 152 nJ;
  - Vsd(-25 A, Vgs 0): 2.20 V at 60 C;
  - Qg(0→5 V, Vds 0): 15.1 nC (datasheet 17.1 nC at Vds 20 V, which
    includes Qgd 2 nC);
  - internal rg: 0.3 Ohm (datasheet 0.4).

## 5. Convergence evidence

- **Stop criterion** (BOUNDARY). The relative cycle-to-cycle change of every
  capacitor voltage and inductor current is below 1e-3. That covers the
  divider, flying and output capacitors, the eight switch-branch voltages
  and the five inductor currents. The change is taken at the quiet sample
  τ = 35 ns, relative to max(|x|, 0.1 V or 1 A).
- **Extra acceptance tests** (PROJECT_DECISION): |P_out/250 - 1| < 1e-3 on
  the same period, and a loss change below 0.005 W/period. Accepted points
  show:
  - rel change 1e-5 to 7e-4;
  - power error ≤ 9.7e-4;
  - geometric tail estimate of the remaining loss drift: |tail| ≤ 0.05 W on
    optima and centres, ≤ 0.23 W on a few sweep points.
- **Periods needed, plain simulation from A59's z*.** Brute-force runs
  (`*_brute.json`, no acceleration, fixed timing and Ton) at the primary
  centres:
  - **Large-ripple:** first period below 1e-3 is period 27. P_loss after
    40 periods is 64.178 W, vs the accelerated solve's 64.182 W.
  - **Baseline:** first below 1e-3 is period 16. It gives 44.594 W vs
    44.570 W.
  - The accelerated solves used 32-256 periods per point (warm-started).
- **Timestep** (BOUNDARY): 25 ps vs 50 ps max step at the primary optima:
  - large-ripple 61.086 → 61.060 W (-0.026) and 61.201 → 61.210 W (+0.009);
  - baseline 43.740 → 43.753 W (+0.013).
  - Ton and timing unchanged.
- **Energy bookkeeping.**
  - The Python trapezoid of V_src·I_src equals LTspice's own `.meas INTEG`
    (e.g. 60.80008 W both).
  - The stored-energy correction matters. The raw P_in - P_out of the
    large-ripple optimum was 60.80 W at 50 ps and 61.16 W at 25 ps; the
    corrected values are 61.20 and 61.21 W.
- **Parallel-device symmetry.** With all 20 gate currents saved, the maximum
  difference between parallel devices is 4e-11 A. Gate energy is therefore
  measured on device A × group count.
- **Model-integration check.**
  - LTspice 26.0.2 does not integrate a charge-defined capacitor written as
    `Q=f(v(a,b))` charge-conservingly: a 2 nF `Q=2n*v(d)` absorbs 3.20 nC
    by 2 V instead of 4 nC. The same element written with `x` is exact.
  - The vendor model writes all its nonlinear capacitances in the
    `v(a,b)` form. At default reltol, or at 0.2 ps steps, its measured Qoss
    depends on current and step (19.1 or 9.9 nC at 12 V instead of 26.4).
  - At the reltol 1e-4 used here with ≥ 2 ps steps it is correct (26.43 nC).
  - An identity rewrite into `x` (`EPC2067X`, `fetch_epc2067_model.x_form`;
    0.1 pF cross term kept verbatim) is exact at every rate and step.
  - All eight accepted optima and centres were re-run with EPC2067X
    (`*_xcheck.json`). |ΔP_loss| ≤ 0.011 W, and Pout and channel timing are
    unchanged. **The results do not depend on this LTspice behaviour.**
- **NOT_CONVERGED points, kept and not used:**
  - **Three baseline R1.0 points** (4.35/3.35, 4.35/2.85, 4.55/2.95). The Ton
    secant took a noise-driven slope of ~3 W/ns, so Ton oscillated by
    ±0.3 ns. A slope clamp (10-60 W/ns) was added and all three were
    re-solved from a regulated neighbour. They are regulated as `_v2`.
  - **Baseline R1.0 (4.05, 2.85)** was attempted twice with the clamp
    (`r4.050_f2.850.json`, `_v2`). Neither reached a period-1 orbit in 256
    periods: a slow ~30-period oscillation remains, with rel change 7e-4 to
    1.2e-2 and P_loss 43.39-43.73 W. The d_fall extension stops there. A
    true optimum up to ~0.35 W below 43.74 W would only widen the
    large-ripple deficit.
  - **Centre searches** (`*_centre_search.json`) are timing locators, not
    results. The large-ripple R1.0 search did not converge: its channel rise
    dead time moves ~2x the command step. Its snapped centre (3.55, 3.00)
    was solved normally.

## 6. PROJECT_DECISIONs and classifications

`EXTERNAL_DEVICE_DATA`: the EPC2067 subcircuit, block SHA-256 `b1d201cc7ab403f7...`,
2734 characters, identical on four GitHub mirrors, not committed.

`PROJECT_DECISION` (declared in BOUNDARY): floating 0/5 V source per device
with R_drv ∈ {0.3, 1.0} Ohm, and Tj = 60 C.

`PROJECT_DECISION` (this experiment):

1. **Channel-referenced sweep centre.** The command dead times were moved
   (secant per edge type) until the four-phase mean channel dead times equal
   A59's 1.95/0.65 ns (large-ripple) and 2.15/1.15 ns (baseline), then
   snapped to 0.05 ns. The BOUNDARY ±0.3 ns / 0.1 ns sweep runs around that
   point, d_fall first.
2. **Outward extension.** The sweep is extended one 0.1 ns step at a time
   while the optimum sits on the grid edge (as in A59), plus a second-pass
   d_fall line at the optimum d_rise.
3. **PULSE ramps.** The 0.1 ns ramps start at the commanded window boundary,
   a uniform 0.05 ns delay at 50%.
4. **Channel on/off instant** = internal Vgs crossing k2(T). "Vds reached
   zero" = branch Vds ≤ 0.5 V. Reverse conduction = Vds < -0.5 V.
5. **Sampling instant.** The sampling/restart instant is τ = 35 ns, where all
   gates have been static for ≥ 15 ns. Warm restarts use DC-constrained
   `.ic` on 13 nodes and 5 inductor currents. LTspice honours the inductor
   ICs to ~2 mA (16 mA on L1), which only affects the initial guess.
6. **Stop-criterion floors** of 0.1 V / 1 A, plus the loss-stable 0.005 W/period
   test. P_loss includes the stored-energy correction (linear passives,
   exact) over the measured period.
7. **Acceleration (NUMERICAL_IDEALIZATION).** Between chunks the solver uses
   reduced-rank extrapolation of the period-map fixed point, a secant on the
   extrapolated power, and the slope clamp. The accepted period is always a
   plain simulated period that passes all tests. The brute-force runs check
   this within 0.003 / 0.024 W.
8. **Solver settings.** Max step 50 ps (25 ps check), reltol 1e-4,
   trapezoidal, numdgt 15 (double-precision raw).
9. **Metering.** A 0 V ammeter in series with each switch group, for
   metering only. Gate energy is taken on device A × count.
10. **Loss-decomposition thresholds** (Section 3) and the Coss displacement
    correction from the vendor Q(V) at 0.1 A.
11. **R_drv 0.3 case.** A full BOUNDARY sweep was run rather than the
    allowed fallback of "centre + transferred optimum". The transferred point
    was also solved. It is large-ripple (2.90, 1.05) and is in
    fall-edge shoot-through (channel -0.39 ns, 39.47 W). This shows that
    command offsets do not transfer between drivers.
12. **Raw reader.** An own numpy reader of LTspice's `.raw` (the A52 format,
    plus the all-double layout that numdgt produces).

## 7. Deviations from BOUNDARY

1. **Sweep centre.** The sweep is centred on the channel-referenced
   equivalent of A59's timing, not on A59's command values. Those are
   shoot-through with the vendor gate (Section 0). The literal A59-timing
   points were run, regulated and are reported (163.75 W / 114.13 W).
2. **Sweep range.** It exceeds ±0.3 ns through declared extensions:
   - large-ripple R1.0 d_fall down to 2.20 (centre 3.00);
   - large-ripple R0.3 d_fall to 1.25 (centre 1.75);
   - baseline R1.0 d_fall to 2.95 accepted (2.85 not converged) and d_rise
     3.95-4.65.

   For the large-ripple R1.0 design, d_rise was swept at d_fall 2.40. The
   final d_fall 2.30 was found in the second pass, and d_rise was not re-swept
   there. It is flat: 3.65-3.85 → 61.20-61.29 W at 2.40.
3. **Temperature.** `.temp 25` was not run, per the coordinator's close-out
   instruction. Both cases are at 60 C. The static 25 C check is in
   Section 4.
4. **Added tests.** Stricter-than-BOUNDARY acceptance (loss-stable) and the
   stored-energy correction were added.
5. **Added checks.** The model-integration check, the EPC2067X re-runs, the
   static Rds/Coss/Ciss characterization, the loss decomposition and the
   brute-force runs were added.
6. **Superseded records** are kept in `runs/xform_check/`:
   - a first Coss table taken at 1 A with default reltol (wrong, see
     Section 5);
   - a model-check draft whose gate-ramp test read the external gate node;
   - one decomposition made with the superseded table;
   - a partial EPC2067X centre search.

   The first terminal-energy (uncorrected) decompositions `*_decomp.json`
   remain in `runs/`; the corrected ones are `*_decompc.json`.

## 8. Limits

- **Layout.** No loop or common-source inductance is modelled. Common-source
  inductance would slow the turn-off further, and a loop inductance would add
  ringing. The real turn-off loss could be higher or lower.
- **Gate driver.** It is symmetric (same R for pull-up and pull-down). Real
  GaN drivers often have a stronger sink. The result is sensitive to this:
  24 W of the large-ripple loss moves between 1.0 and 0.3 Ohm. A split
  driver would narrow the gap further.
- **Vendor model.** Its turn-off channel dynamics at ~95 A per device are
  EPC's fit and are not independently verified here. Its capacitances have
  no temperature dependence.
- **Out of scope.** One Tj for all devices, no thermal model, no inductor
  loss (A61), 250 W only (A62), and no device spread.
- **Timing.** Common dead times across phases. The phase-4 edge differs
  slightly in channel timing.

## 9. Reproduction

```
python3 fetch_epc2067_model.py --all          # -> vendor/EPC2067.lib, vendor/EPC2067X.lib (git-ignored)
python3 test_a64.py -v                        # schedule vs A58, PULSE, z* ordering, RRE, block hash, x-form
export A64_WORKDIR=/tmp/a64                   # short path for LTspice/Wine
python3 run_a64.py --design zvs      --stages center,sweep,repair,extend_fall,step,decomp,xcheck,literal,brute
python3 run_a64.py --design baseline --stages center,sweep,repair,extend_fall,step,decomp,xcheck,literal,brute
python3 run_a64.py --design zvs      --case 0.3:60 --stages center,sweep,transfer,decomp,xcheck
python3 run_a64.py --design baseline --case 0.3:60 --stages center,sweep,repair,decomp,xcheck
python3 run_a64.py --design zvs --stages modelcheck,coss,static --log _model
python3 run_a64.py --design zvs --stages wave ; python3 run_a64.py --design baseline --stages wave
python3 build_a64_results.py                  # results.json (never overwritten; writes results_vN.json)
```

At most two LTspice processes were run at once (one driver per design).
No file outside this directory was modified.
