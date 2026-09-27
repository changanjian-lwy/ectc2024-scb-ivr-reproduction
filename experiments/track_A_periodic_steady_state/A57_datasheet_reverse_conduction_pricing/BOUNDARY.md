# A57 - pricing A56's dead-time conduction with the EPC2067 datasheet reverse characteristic (BOUNDARY)

Track: A. Classification: `SENSITIVITY_ONLY` post-processing of A56's
committed orbits with one new `EXTERNAL_DEVICE_DATA` input. No new orbit
solve, no SPICE. Not a P24/P25 reproduction. Per user direction 2026-09-28:
check whether the math-model session's new work supplies the missing
reverse-conduction number; if not, obtain it from public data.

## 0. Why this experiment exists

A56 found that, at equal 250 W, the best all-eight-ZVS point
(`L=0.627406 nH`, 2.15 ns) has a partial-loss proxy 3.18 W below the
regulated nominal baseline, and named the unsourced reverse-conduction drop
as the largest open risk (break-even constant drop 0.90 V at 2.15 ns,
0.32 V at 4.3 ns).

The math-model session's new, uncommitted D05
(`symbolic_derivations/02_P25_native/D05_REVERSE_COMPLEMENTARITY.md`,
`src/scb_ivr/p25_reverse_contract.py`) adds an explicit
`constant_drop_surrogate` branch with dissipation `Vf*r`, the same form
A56's break-even used. It states it supplies **no** real reverse-drop value
("不是我们获得了实际反向压降"), is P25 three-phase, instantaneous only, and not
wired to any periodic solver. It is consistent with this experiment but does
not supply the number. This experiment does not import it (uncommitted work
of another session).

## 1. What A56's model already represents (read from code, not assumed)

A56/A51 turn a channel on at the natural `Vds=0` crossing, or at the
commanded window end, whichever is first
(`orbit_diagnostics.dead_time_surrogate_exposure`: natural admissions only).
After a natural crossing the remainder of the commanded dead-time window is
conducted by the ideal channel through `Ron`. Therefore:

- **Scenario A - ideal adaptive turn-on** (gate follows the zero crossing
  with zero delay): exactly A56's model. A56's proxies stand as computed.
- **Scenario B - fixed dead time** (gate turns on only at the commanded
  window end, the A51 symmetric windows): the same current-time must pass
  through the OFF device's third-quadrant channel at `VSD(I)`, not through
  `Ron`.

This experiment prices Scenario B. Scenario A is not changed.

## 2. The external data (EXTERNAL_DEVICE_DATA)

- EPC EPC2067 datasheet, "Revised October 21, 2021" (same revision as
  `src/scb_ivr/device_library.py`), URL
  `https://epc-co.com/epc/Portals/0/epc/documents/datasheets/epc2067_datasheet.pdf`.
  The script records the SHA-256 of the file it read. The PDF itself is not
  committed.
- Figure 8 "Typical Reverse Drain-Source Characteristics", `VGS = 0 V`,
  25 C and 125 C curves, per device. Digitized from the PDF's vector paths
  (Bezier control points), mapped to axes by a least-squares fit to the tick
  label positions; zero current anchored to the curve's own flat `ISD=0`
  segment. Digitization uncertainty is reported.
- Table value `VSD = 1.2 V typ at IS = 0.5 A, VGS = 0 V` ("defined by design,
  not production tested"): used only as the most ZVS-favorable constant floor,
  not as the operating-current value.
- The datasheet note that negative gate drive raises the reverse drop: a
  `0 V` OFF gate is assumed (EPC's recommendation). Negative OFF bias would
  make Scenario B worse for every candidate with reverse exposure.

## 3. Method (first-order pricing, the same contract as A56's break-even)

For each A56 orbit, for each natural-admission interval stored in
`capacitive_accounting.json` (`abs_charge_c = integral |i| dt`,
`i2_dt_a2s = integral i^2 dt`, `admitted_duration_s`), with the branch
current shared equally by the parallel devices (`NHS=2`, `NLS=3`,
`P24_EXPLICIT` population):

    E_rev(event) = VSD(I_mean / n) * abs_charge_c,   I_mean = abs_charge_c / duration
    P_B = P_A(proxy) - P_channel_metered_in_intervals + f_sw * sum E_rev

Using the event-mean current is justified only because the stored
rms/mean ratio is <= 1.05 in every event; the script also evaluates
`VSD(I_rms/n)` and reports the spread. Orbits are **not** re-solved with the
clamp: the node sitting at `-VSD` instead of `~0` for ~1-4 ns is a small
perturbation of the regulated operating point, and is neglected (stated).

Separately listed, not in the headline: a gate turn-on from `-VSD` recharges
the node by `VSD`; order-of-magnitude `0.5*C_node*VSD^2*f_sw` per event with
`C_node = 13.0 nF` (A56's measured high-side node capacitance, used for all
events as an approximation).

Also reported: the residual per-edge reverse time `t_r` (equal for every
admitted edge of both designs) at which the ZVS point loses its Scenario A
advantage - the dead-time precision a tuned (adaptive or asymmetric) design
would need. Illustrative, not a driver specification.

## 4. Provenance

| Value | Source | Category |
|---|---|---|
| `VSD(ISD)` curves, 25/125 C, `VGS=0` | EPC2067 datasheet Fig. 8 | `EXTERNAL_DEVICE_DATA` |
| `VSD=1.2 V` at 0.5 A | EPC2067 datasheet table | `EXTERNAL_DEVICE_DATA` |
| `NHS=2`, `NLS=3` | P24 Table 3 | `P24_EXPLICIT` |
| Orbits, proxies, exposure moments | A56 committed files | inherited `SENSITIVITY_ONLY` |
| Scenario A/B split, equal current sharing, no re-solve, `C_node` choice | This document | `PROJECT_DECISION` |

## 5. What the result can and cannot decide

Decides: under fixed symmetric dead time with the datasheet's typical
reverse characteristic, whether A56's ZVS advantage survives, and how
tight per-edge dead-time tuning must be for it to survive.

Cannot decide: whether P24's hardware used adaptive dead time; gate-drive,
magnetic, thermal loss; device-to-device spread (the curve is "typical");
the Co(er)/Co(tr) question; any paper reproduction.

## 6. Constraints

Read-only use of A56 files. Do not modify `src/scb_ivr/`, `results/`,
`paper_locked/`, or any A37-A56 file. Do not commit the other session's
uncommitted files.
