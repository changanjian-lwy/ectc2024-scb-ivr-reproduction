# A90 - junction temperature 125 C in the P24 module (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION` + `EXTERNAL_DEVICE_DATA`. Written before any
run.

## 1. Question

Every result from A86 to A89 uses EPC2067 data at 25 C. The device's
public data also give 125 C, the datasheet's hot curves.

**With every switch at a junction temperature of 125 C:**
- does the adopted module keep every phase soft and meet criterion 2?
- how much do the losses rise?
- how does the timing window of the timed low side change?

This is one factor: a uniform junction temperature, applied consistently
to every temperature-dependent device parameter that has public data. It
is a fixed boundary case, not a thermal model; the thermal network is the
next level.

## 2. Data: public, reliable, reproducible

The source is the EPC2067 datasheet, "Revised October 21, 2021", SHA-256
8271d9eb...2324f, as A57, A59 and A86-A89.

| parameter | 25 C (A86-A88) | 125 C (here) | source, and check |
|---|---|---|---|
| **RDS(on)** | x 1 | **x 1.586** | Fig. 9, normalised RDS(on) vs TJ, ID 37 A, VGS 5 V. Digitised here (`digitize_epc2067_fig9.py`: vector paths, tick residual 1.06 C / 0.004). **Check:** EPC's public SPICE model (library v1.93, forward channel equation with its temperature coefficients, same conditions) gives 1.582, and agrees within 0.25% over 0-150 C (`a90_check_fig9_vs_epc_model.py`). The model's 25 C value, 1.280 mOhm, matches the printed typical 1.3 mOhm. |
| **reverse conduction** | Vf 2.0894 V, R 6.013 mOhm per device | **Vf 1.9483 V, R 8.948 mOhm per device** (fit error at most 38 mV over 10-100 A) | Fig. 8 125 C curve (A57's digitisation, read-only), fitted as A87. **Check:** against EPC's model at 125 C, within 5-35 mV over 1-400 A (A87 `a87_fig8_vs_epc_model.json`). |
| **Coss(V)** | Fig. 5a | **unchanged** | The datasheet gives capacitances at TJ = 25 C only, and none of the EPC model's six capacitance expressions depends on temperature. |

## 3. Model used, and how temperature enters

**The physical model:** A88's simulator, copied as `a90_transient.py`,
with a `--tj` option.
- The module's per-phase series R is the duty-weighted RDS(on) (A72:
  1.55 mOhm per device, the datasheet's 25 C maximum, with 2 high-side and
  3 low-side devices in parallel and D = 1/12). The inductor DCR and
  copper are zero, as in Track A.
- So at TJ the whole R scales by Fig. 9's factor:
  R(125 C) = 0.54 x 1.586 = 0.856 mOhm.
- The reverse fit uses Fig. 8 at the chosen temperature. The code allows
  25 C and 125 C only, the curves the datasheet gives.
- Coss(V) and everything else are unchanged.

**Controller:** A88's adopted rules, unchanged:
- predictive valley high side, learning at restarts;
- timed low side with the zero-crossing corrector;
- trim 0.5;
- restart 20 / 400 ns;
- ki 0.25 ns/V;
- t_d 10 ns.

**Gate:** `--tj 25` must replay A88 run r1 bit-identically.

**A note on the device library** (`src/scb_ivr/device_library.py`, not
changed here): its EPC2067 entry `rds_on_typ_ohm = 1.55e-3` is the
datasheet's maximum; the typical value is 1.3 mOhm. The module's R, and
this experiment, keep A72's value. The 125 C R is therefore the 25 C
maximum times the typical temperature factor.

## 4. Runs

A88's module and controller, zero start, 388.61 us.

| run | target | TJ | purpose |
|---|---:|---:|---|
| r0 | 3% | 25 C | gate (= A88 r1) |
| r1 | 3% | 125 C | main |
| r2 | 2% | 125 C | P24's stated value |
| r3 | 5% | 125 C | |
| r4 | 7.5% | 125 C | |

## 5. Predictions (written before the runs)

- **Conduction loss** rises by the R factor, since i^2 barely changes:
  about 12.2 to about 19.4 W at 3%.
- **Ton** rises by about 0.3-0.5 ns. The loop compensates the extra IR drop
  of about 0.32 mOhm x 62.5 A = 20 mV per phase, at about 54 mV/ns.
- **P_rev stays 0 W.** The timed low side keeps the node above about
  -0.65 V, far from -1.95 V.
- **The low-side dead time** is unchanged within about 0.02 ns: Coss and
  the current at the high-side turn-off hardly change.
- **Soft switching and phase 4** are unchanged within the corrector
  dither. The extra R adds little damping to the valley ring (its Q stays
  large). Turn-on voltages change by less than 0.05 V.
- **Criterion 2** is as at 25 C: pass at 3% and 5%; the dither near 1 A
  at 2% and 7.5% remains a margin question.
- **The free window after the zero crossing** narrows with the reverse
  threshold, from 2.09 to 1.95 V:
  - phase 4 about 0.15 ns (25 C: 0.16);
  - phases 1-3 about 0.21 ns (25 C: 0.22).

## 6. Mathematical-model counterpart (D48)

D47's timed-low-side event map with the 125 C parameters: R 0.856 mOhm,
Vf 1.9483 V, R 8.948 mOhm per device.
- Regulated, valley- and crossing-consistent orbits at the same four
  targets.
- The free window measured as in D47 Section 8.

D47 and its script are unchanged; a new script passes the parameters.

## 7. Decides / does not decide

Decides:
- whether the adopted single module works at TJ = 125 C with the public
  device data;
- the hot-corner losses;
- the timing window.

Does not decide:
- temperature gradients and a self-consistent junction temperature (the
  thermal network, next level);
- any temperature dependence of Coss (no public data);
- dynamic RDS(on) (current collapse);
- gate-driver drift;
- package and PCB parasitics.
