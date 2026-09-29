# A65 - A64 with a real gate driver: TI LMG1210's output stage (BOUNDARY)

Track A, `SENSITIVITY_ONLY`. Written and committed before any accepted run.

## 1. Question

A64 left the gate driver as a free parameter: a symmetric resistor per
device, 1.0 Ohm or 0.3 Ohm. The answer swung from +17.35 W to +1.20 W
(large-ripple minus baseline at 250 W, 60 C). Which side of that range does
a real driver fall on?

## 2. Driver choice and what the datasheets already settle

P24 sizes its converter "without considering GaN gate drivers"
(`P24_EXPLICIT`, Sec. V). Its 5 MHz, 48 V -> 1 V, 4-phase point has a
high-side on-time of `Ton = nP*Vo/(f*Vin) = 16.7 ns` (P24 Eq. 3). A64's
regulated high-side gate windows are 14.6-16.3 ns.

- **P25's own driver cannot be used.** The only built prototype of this
  author group (P25, 12 V, 0.5 MHz) uses Infineon 1EDBx275F
  (`P25_SUPPLEMENT`, Table III). Its minimum input pulse width that changes
  the output is 15 / 19 / 23 ns (min / typ / max, datasheet Table 15). A
  typical part suppresses P24's high-side pulse. It is excluded.
- **Chosen: TI LMG1210** (`EXTERNAL_DEVICE_DATA`), a half-bridge GaN driver
  specified up to 50 MHz, with a 4 ns maximum minimum pulse width and a
  5 V supply. Output stage from datasheet Figs. 1-2 (typical source and
  sink current vs output voltage). Digitized from the PDF's vector paths
  by `digitize_lmg1210_output_iv.py`; axis residuals < 0.5 mV / 0.5 mA.
  The PDF is not redistributed; its SHA-256 is checked. The curves peak at
  1.68 A source and 3.64 A sink, above the table's typical 1.58 A and
  3.1 A. The curves are therefore the stronger, optimistic driver. That
  favours the large-ripple design, which needs a fast turn-off.
- **One driver per switch cannot drive P24's high side** (pre-boundary
  feasibility check, disclosed here). Two EPC2067 need
  2 x 15.1 nC = 30 nC to reach 5 V. At <= 1.68 A that takes >= 18 ns,
  more than the 14.6-16.7 ns on-time. A 3-period LTspice smoke run confirmed
  it: from A64's R1.0 large-ripple optimum, with one LMG1210 output per
  switch, the high-side internal Vgs peaked at 3.18 V. That arrangement
  (`LMG1210_SW`) is therefore reported as infeasible and is not swept.
- **Primary case: one LMG1210 output per device (`LMG1210_DEV`).** This is
  the strongest arrangement commercial parts allow. It is optimistic: it
  ignores the 20 drivers' placement, their supplies and their
  propagation-delay spread.

Plateau-equivalent resistance, used only as the initial timing guess: at
the A64 turn-off plateau (internal Vgs 2.3-2.6 V, A64 waveforms), the
LMG1210 sink in series with the model's 0.3 Ohm rg is equivalent to
R_drv ~ 0.61 Ohm per device (`LMG1210_DEV`), or ~1.38 Ohm for `LMG1210_SW`.

## 3. Model and procedure (unchanged from A64 unless listed)

A64's code is copied into this directory. A64's files are not modified.
Everything is A64's BOUNDARY:

- A59's four-phase ladder;
- EPC's EPC2067 subcircuit, re-fetched by the copied
  `fetch_epc2067_model.py` (hash b1d201cc7ab403f7...), git-ignored;
- 2 high / 3 low devices per switch;
- 60 C;
- regulation to 250 W;
- 50 ps maximum step;
- A64's stop criteria, centre search, +/-0.3 ns sweep and extensions.

Changes:

1. **Gate drive.** Per device, a 5 V DC supply `V_G`, a 0/5 V command
   `V_M` (PULSE, as in A64), and two behavioural current sources:
   - pull-up: `w * I_src(Vgs)/n`;
   - pull-down: `(1 - w) * I_snk(Vgs)/n`;
   - `w = V_M/5`, `n` = devices per driver output.

   Outside 0-5 V the tables continue linearly with the curves' end slopes.
   The gate-drive energy is the energy `V_G` delivers, the same metric as
   in A64. There is no gate-loop inductance, as in A64. The driver's common
   ~10 ns propagation delay is absorbed by the re-tuned command timing.
2. **Warm start.** The centre search starts from A64's `R_drv 1.0 Ohm`
   optimum state of the same design, which it reads only. The seed changes
   convergence speed, not the periodic orbit.
3. **Regression gate.** With the resistor driver, A65's netlist builder must
   emit A64's netlist line for line; only the two header comment lines may
   differ. This was checked before this BOUNDARY: 116/116 lines, 2 header
   differences.
4. **Negative command dead times allowed (amendment, before any record).**
   A64's code floored command dead times at +0.05 ns. That floor never
   bound in A64, where command dead times were >= 1.35 ns.

   With LMG1210's ~1.5 A pull-up, the incoming channel turns on about 1 ns
   later than the outgoing one turns off, even at zero command dead time.
   The first centre-search chunks of the large-ripple design drove `d_fall`
   to the floor, with the channel fall dead time still ~1 ns (target
   0.65 ns). A floored optimum would have overstated the large-ripple loss.

   The runs were stopped before any record was written. Then:
   - the floor is `-2.5 ns` (command overlap; the channels themselves still
     must not overlap, and the loss shows it if they do);
   - A64's edge analysis computed the incoming command time as
     `(t_in - t_out) mod T`. That maps a negative offset to almost a period
     later. It now wraps the signed offset to (-T/2, T/2]. Its search
     window starts at the earlier of the two commands and ends 8 ns after
     the later one.

   Both are identical to A64 for positive dead times; unit tests cover this
   (13 tests).

## 4. Decides / does not decide

Decides:

- whether the tuned large-ripple design beats the tuned baseline at 250 W,
  60 C, with the strongest commercially plausible driver arrangement
  (`LMG1210_DEV`);
- how the result compares with A64's two resistor cases.

Does not decide:

- custom or in-package drivers;
- the realistic timing accuracy. LMG1210's minimum dead time spreads
  -0.55 / 0.8 / 3.1 ns and its high-/low-side matching is up to 3.4 ns.
  Both are far above the ~0.1-0.3 ns precision that the tuned optima use.
  This is reported, not modelled;
- the temperature dependence of the driver or the device beyond A64's 60 C;
- gate-loop inductance.

## 5. Records

`runs/*.json` (never overwritten), `logs/`, `results.json` built by
`build_a65_results.py`, and `RESULTS.md`.
