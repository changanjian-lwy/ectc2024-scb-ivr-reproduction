# A58 - asymmetric fixed dead time: can tuned (non-adaptive) timing keep the rated-load ZVS advantage? (BOUNDARY)

Track: A. Classification: `SENSITIVITY_ONLY`, a control-boundary extension
of A51/A56 with A57's datasheet reverse pricing. Not a P24/P25
reproduction. Per user direction 2026-09-28 ("你接着做") after A57.

## 0. Why this experiment exists

A57 showed that A56's 3.18 W ZVS advantage at 250 W is the ideal
adaptive-dead-time limit. Under the A51 scheduler's single symmetric fixed
dead time (2.15 ns on both edges), the EPC2067 datasheet reverse drop
(2.27-2.52 V at operating current) makes the ZVS point 7.06 W worse. The
ZVS point survives only if each edge's residual reverse conduction stays
below ~0.44 ns.

The symmetric window is the obvious weakness. At the ZVS point, the
high-side (rising) transition needs ~2.05 ns, but the low-side (falling)
transition needs only ~0.5-0.7 ns at +215 A. One shared value must cover
the slow edge and so wastes ~1.45 ns of reverse conduction on the fast edge.
A real driver can set the two dead times separately. This experiment asks
whether a realistic **fixed** (non-adaptive) setting of two dead times can
recover the advantage, against an **equally tuned** hard-switched baseline.

## 1. Declared control boundary (`PROJECT_DECISION`)

- **Two dead times**, common to all four phases:
  - `d_rise`: low-side off -> high-side on (the high-side ZVS edge);
  - `d_fall`: high-side off -> low-side on (the low-side edge).
  A per-phase setting is out of scope. It would be a further decision.
- **Window placement**: each window is centered on its commanded edge, as in
  A50/A51/A55/A56 (`[on - d_rise/2, on + d_rise/2)`,
  `[off - d_fall/2, off + d_fall/2)`). With `d_rise = d_fall` the schedule is
  identical to A56's. This must be proved bit-for-bit by a test.
- **Regulation**: `Ton_cmd` is regulated to `mean(Vout^2/R) = 250 W`, with
  the 4 mOhm load fixed, exactly as in A56 (same outer search policy, reused
  from A56's `run_regulated_candidate.next_ton`, same `1e-3` solver
  tolerance, same `+/-250 A` project screen on orbits and every probe).
- **Dynamics**: A56's, unchanged. The channel turns on at the natural zero
  crossing or at the window end, whichever is first. Only the window
  lengths change.

Implementation (verify, don't assume): the A50/A51 scheduler reads the
scalar `boundary.dead_time_s` in `commanded_pwm_mode` (imported by name into
several modules), `next_pwm_edge_s`, `period_intervals` and `period_start_s`.
A58 does **not** edit those files. It supplies asymmetric versions that
dispatch on a new boundary subclass and are installed by a scoped rebinding
in every module namespace that holds them. A58 processes are standalone,
serial and single-threaded, as in A55/A56. Tests must prove:

1. With `d_rise = d_fall = 2.15 ns`, the period map from A56's regulated
   `z*` is bit-identical to A56's own boundary.
2. With `d_rise != d_fall`, every commanded mode seen through every patched
   namespace matches the analytic asymmetric schedule. Every interval has
   its declared window length. Every turn-on/turn-off verdict's window has
   the correct length.
3. No solve or metering path reads the scalar `dead_time_s`. Overwriting it
   with a different value leaves the period map bit-identical.

## 2. Loss objective (all partial electrical-loss proxies at 250 W)

For each regulated point:

- `P_A` (adaptive limit, A56's definition): A55 branch-meter channel loss,
  plus the hard- and partial-hard-switch capacitive energy the coarse meter
  misses. Missed energy per event is `E(h->0) - E(orbit)` on A56's 500 ps
  post-event window, with `E(h->0)` Richardson-extrapolated from 0.05/0.025
  ps re-integration (A56's method, both sides).
- `P_B` (fixed dead time, the headline): `P_A`, minus the Ron loss inside
  natural-admission remainders, plus A57's datasheet reverse loss
  `VSD(I/n) * Q` (Fig. 8, 25 C, `VGS=0`; 125 C and the 1.2 V floor as
  sensitivities). First-order, exactly A57's contract.
- Listed separately, not in the headline: A57's turn-on recharge estimate
  `0.5*C_node*VSD^2*f_sw`.
- Recorded, not used as the objective: the coarse-step source-side balance
  `P_in - P_out`.

A window shorter than the transition gives a partial hard turn-on. This is
paid for by the capacitive term, not by reverse conduction. The optimum
therefore balances the two, and it may lie below the natural transition
time.

## 3. Candidates and search

Two designs, both from A56 (EPC2067, population-corrected Ron, same passives):

- **ZVS design**: `L = 0.627406 nH`, seeded from A56 `old_critical_dt_x1`.
- **Baseline**: `L = 1.4667 nH`, seeded from A56 `nominal_dt_x1`.

Grid, declared before any run:

- ZVS: `d_rise` in {2.15, 2.0, 1.9, 1.8, 1.6} ns x `d_fall` in
  {2.15, 1.2, 0.9, 0.8, 0.7, 0.6, 0.5} ns.
- Baseline: `d_rise` in {2.15, 1.0, 0.5} ns x `d_fall` in
  {2.15, 1.6, 1.4, 1.3, 1.2, 1.1, 1.0, 0.9} ns.

Search order: continuation, with no raw re-seeding. Phase 1 sweeps `d_rise`
at `d_fall = 2.15 ns` from the A56 anchor. Phase 2 sweeps `d_fall` downward
along each `d_rise` line, each point seeded by its neighbor. Lines run as
independent processes. A point that cannot regulate is recorded as such; it
is a result, not a failure to patch. If the optimum lies on a grid edge,
one extension step outward along that axis is allowed, and it must be
reported as an extension.

Step refinement: re-solve the best ZVS point and the best baseline point at
31.25/2.5 ps and confirm their ranking, ZVS verdicts and `Ton_cmd`.

## 4. Provenance

| Value | Source | Category |
|---|---|---|
| Two-dead-time control, centering, common across phases | This document | `PROJECT_DECISION` |
| Regulation to 250 W by `Ton_cmd`, 4 mOhm load | A56 | `PROJECT_DECISION` (inherited) / `P24_EXPLICIT` |
| `VSD(I)` Fig. 8, 1.2 V floor | A57 digitization of EPC2067 datasheet | `EXTERNAL_DEVICE_DATA` |
| EPC2067 Ron/Coss, `NHS=2`/`NLS=3` | `device_library.py`, P24 Table 3 | `EXTERNAL_DEVICE_DATA` / `P24_EXPLICIT` |
| L values, seeds | A56 | `SENSITIVITY_ONLY`, inherited |
| Grid values, tolerances, steps | This document | `NUMERICAL_IDEALIZATION` |

## 5. What the result can and cannot decide

Decides: under two common fixed dead times, with the datasheet's typical
reverse characteristic, whether the best-tuned ZVS design has a lower
partial-loss proxy than the best-tuned hard-switched baseline at 250 W,
and by how much. Also decides which edge limits it.

Outcomes, all valid:

- **Tuned ZVS < tuned baseline**: fixed timing can keep the advantage. Report
  the required settings and their margin to each edge's natural transition
  time, which is the timing accuracy the design needs.
- **Tuned ZVS >= tuned baseline**: even with tuned fixed timing, rated-load
  ZVS does not pay in this model. Only an adaptive/per-edge controller
  could recover it.
- **Mixed or not regulable**: report per point.

Cannot decide: driver delay/jitter, per-phase or cycle-by-cycle adaptive
control, gate-drive, magnetic, thermal or package loss, Coss nonlinearity
(Co(tr) linear, as in A56), or a clamp-resolved orbit (first-order reverse
pricing as in A57), hardware efficiency or paper reproduction.

## 6. Constraints

Do not modify `src/scb_ivr/`, `results/`, `paper_locked/`, or any A37-A57
file. Never overwrite a result JSON. Retain failed points. Do not commit
another session's uncommitted files.
