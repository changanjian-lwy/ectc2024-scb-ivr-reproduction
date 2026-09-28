# A64 - SPICE cross-check of the A59 tuned comparison with EPC's own EPC2067 device model (BOUNDARY)

Track: A. Classification: `SENSITIVITY_ONLY` verification of A59. Not a
P24/P25 reproduction. Part of the user's 2026-09-28 direction to finish all
self-doable work before asking the advisor; a verification line run
separately from the main line.

## 0. Why this experiment exists

A56-A59 use ideal switches: an instant channel with a fixed Ron,
datasheet-fitted Coss(V) (A59), and reverse conduction priced after the fact
from Fig. 8 (A57, first-order). EPC's vendor SPICE model of EPC2067
contains all three physically:

- a gate- and temperature-dependent channel;
- third-quadrant conduction;
- charge-based nonlinear capacitances.

It also has finite gate charge, so a hard turn-on has V*I overlap loss that
the ideal model does not have. Running both A59 tuned designs through the
vendor model checks A59's ranking and size with a device model we did not
build.

## 1. Vendor model provenance (`EXTERNAL_DEVICE_DATA`)

`.subckt EPC2067 gatein drainin sourcein` from EPC's `EPCGaNLibrary.lib`
(header: "EPC GaN Power Device Library, (C) Copyright Efficient Power
Conversion Corporation"). EPC's own download page returns HTTP 403 to
non-browser clients. The block was therefore taken from four unrelated
public GitHub mirrors, and all four were byte-identical: 2734 characters,
block SHA-256 starting `b1d201cc7ab403f7`:

- vgreff/LTSpiceLibraries
- hadibadri/GaN-Power-Converter
- adml-upm/ESA_parallel_GaN
- Blade87/LTspice

The repository is public. The EPC library is therefore **not committed**.
A fetch script downloads it and verifies the block hash.

## 2. Circuit

- Node-for-node the A59 descriptor topology (see A52's
  `build_full_netlist.py` for the node map and IC transcription discipline):
  48 V source, source R/L, precharge divider with its diodes OFF,
  `C1..C3 = 3 uF`, `L = 0.627406 nH` (large-ripple) or `1.4667 nH`
  (baseline), `Cout`, and a 4 mOhm load. All passive values are A59's
  boundary values, read from the A59 run records.
- Each high-side switch is 2 EPC2067 in parallel and each low-side switch is
  3 in parallel (P24 Table 3). No separate Coss capacitor is added: the
  vendor model carries its own.
- Gate drive, a `PROJECT_DECISION` declared as a sensitivity: each device
  gets a floating 0/5 V source referenced to its own source, through a
  driver resistance `R_drv`. There are two cases: `R_drv = 0.3 Ohm`
  (strong) and `1.0 Ohm` (typical GaN driver). Command edges switch in
  0.1 ns.
- Temperature: `.temp 25`, plus `.temp 60` as a second case (A59's
  1.55 mOhm corresponds to Tj ~ 60 C, per A60).

## 3. Timing and regulation

- Command timing starts from A59's tuned point for each design: centered
  windows, `d_rise`/`d_fall`, and `Ton_cmd`. With finite gate charge, the
  command dead time is no longer the channel dead time. `d_fall` and
  `d_rise` are therefore re-tuned in SPICE by a small declared sweep
  (+/-0.3 ns in 0.1 ns steps around the A59 values, `d_fall` first). The
  loss-minimizing command values are reported together with the resulting
  channel-level timing.
- `Ton_cmd` is adjusted (secant) until `mean(Vout^2/R) = 250 W` within
  `1e-3`, the same tolerance as A56-A59.
- Initial conditions: A59's regulated `z*`, transcribed as in A52. Run until
  cycle-to-cycle change of all capacitor voltages and inductor currents is
  below 1e-3 relative (report the number of periods), then measure the
  last period.

## 4. Loss measurement (no branch metering)

`P_loss = P_in - P_out` over the last period, where `P_in = mean(V_src *
I_src)` and `P_out = mean(Vout^2/R)` (A56's source-side method). Gate-drive
energy is measured separately from the gate sources. A timestep convergence
check halves `maxstep` at the final points.

## 5. What the result can and cannot decide

Decides: with the vendor model, whether the tuned large-ripple design
still has lower loss than the tuned baseline at 250 W; by how much,
compared with A59's 4.58 W; and how much of the difference is hard-switch
overlap loss that A59 lacks.

Cannot decide: the real layout parasitics (a loop inductance is not
modelled), the real driver, device spread, thermal coupling, inductor loss
(see A61), or paper reproduction.

## 6. Constraints

New files only, inside this directory. Do not modify `src/scb_ivr/`,
`results/`, `paper_locked/`, or any A37-A63 file. Never commit the EPC
library. Keep LTspice file paths short: `.meas` output is lost above about
250 characters (A49 lesson).
