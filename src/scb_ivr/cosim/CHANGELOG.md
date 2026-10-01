# scb_ivr.cosim - changelog

History lives here and in the experiments' BOUNDARY/RESULTS, not in the
code. Each entry names its source and the gate that showed it changes no
result.

## 2026-10-01 (later still) - timed phase-1 turn-off (A99)

- **`rtl/scb_phase.v` (phase 1), new `cfg_lo_pred`.**
  - Each comparator-decided mode-P turn-off sets `dlo` to its on-low
    interval.
  - After `cfg_lo_learn` of them (`lo_timed`), the turn-off is a timed
    edge at t_lon + dlo, followed by the predictive turn-on, and the
    asynchronous front end is no longer armed.
  - dlo then steps +1 LSB when the crossing report is early or below
    `cfg_lo_tgt`, else −1.
- **`rtl/scb_ctrl.v`:** the ports; `dlo1` and `lo_timed1` are outputs.
- **`bridge.py`:** cfg keys `lo_pred`, `lo_learn`, `lo_tgt_ps`.
  - In timed mode it measures phase 1's crossing of i_target with the C
    loop's latch test, used as a measurement only.
  - It reports actual turn-off − crossing (or early) at the turn-off.
  - Output fields are added only when `lo_pred` is set.
- **`tb/`:** 3 new tests (learning then timed; the ±1 update; no arming
  when timed). **42 of 42 pass.**
- **Gates:**
  - `--full` regression PASS;
  - `tests/test_cosim_plants.py` passed;
  - synthesis: 0 problems, 41 605 cells.
- **A99's result:** the timed mode lowers the jitter response of phases
  2-4 by 30-38% and removes the trim's limit cycle.
- **Not adopted yet** (load steps untested). The preset is unchanged.

## 2026-10-01 (late night) - jitter on one side's edges only (A98)

- **`bridge.py`:** `driver.jitter_edges` = `"high"` or `"low"` restricts the
  Gaussian edge jitter to that side's gate edges.
  - Absent or `"all"`: every edge, and the same random sequence as before.
- **Gate:** `scripts/cosim_regression.py --full` PASS (A92 j100 exercises
  the jitter path).
- **The preset is unchanged.** A98's gain-1/4 runs lowered the turn-ons
  before the valley but raised the reverse-conduction loss by more than the
  hard-on loss they saved.

## 2026-10-01 (night) - slots from the two-period average (A97); the preset adopts them

- **`rtl/scb_ctrl.v`:** new input `cfg_slot_avg`.
  - It keeps the period before last (t_per2) and a flag that three phase-1
    turn-ons have been seen.
  - With `cfg_slot_follow` as well, phase k's slot is
    t_ref + (k-1)(T_meas + T_prev)/(2N).
  - With the bit at 0, A93's expression is unchanged.
- **`bridge.py`:** cfg key `slot_avg` (absent = 0).
- **`run.py`:** the provenance's `cfg_path` is project-relative when the
  configuration is inside the project, so published records carry no home
  directory. This is a format change only; `--quick` still passes.
- **`tb/`:**
  - the fixture drives the new input (0 by default);
  - `_phase1_cycle` can hold the current comparator for a different
    period;
  - 3 new tests; **39 of 39 pass**, with A93's 36 unchanged.
- **Gates:**
  - `scripts/cosim_regression.py --full` with the new RTL: A89 r2, A92
    j100, A92 m3p and A93 m3n_both are bit-identical (61-64 s each);
  - `tests/test_cosim_plants.py`: 3 passed;
  - synthesis: 0 problems.
- **`presets/p24_5pct_adopted.json`:**
  - now has `slot_follow`, `slot_avg`, `slot_guard` = 1 and
    `plant_impl` `kernel2` (bit-identical to the `kernel` it named);
  - **A97 adopted these slots**
    (`experiments/track_A_periodic_steady_state/A97_verilog_averaged_period_slots/RESULTS.md`
    Section 7);
  - the preset equals A97's `cfg_n0_avg_guard.json` except for `out` and
    `note`;
  - A92's adopted configuration remains in A92's folder.

## 2026-10-01 (evening) - process check (`scripts/cosim_trace_compare.py`)

**What it checks.** That the trajectory, not only the result, is the same
before and after the clean-up. It uses the opt-in `COSIM_TRACE` in
`bridge.py`.
- A92 n0 runs twice: once with the archived A92 bridge and plant (copied
  verbatim into tmp, with the same checkpoint lines), and once with
  `kernel2`.
- At every checkpoint both runs update a running BLAKE2b hash of t, the
  full state y, the diode flags and the Euler counter. The checkpoints are
  the plant integrated to each gate edge and to each 4 ns window end.

**Result: 125 259 checkpoints, all identical.** Final digest
82f7bab1ecfd3afb3bafee693dcc7e4f in both runs. Both outputs are also
bit-identical to the archived run.

**Wall time, each run alone:** 1444.7 s with the archived code, 54.7 s
with `kernel2` (26 times faster).

## 2026-10-01 (evening) - benchmark against the archived runs (`scripts/cosim_benchmark.py`)

**`--batch`.** A92's 9 configurations, default plant, 4 at a time:
- 147 s in total, 61-67 s per full run (16 s for the 96 us diagnostic);
- all 9 are bit-identical to the archived runs;
- for comparison, the archived batch took 4353-4452 s per run with 8-10
  runs at once.

**`--plants`.** A92 n0, the adopted design, full length. The first four
ran at once, one core each; kernel2 ran alone.

| implementation | wall time | result against the archived run |
|---|---:|---|
| archived A92 bridge and plant (the code before the clean-up) | 1998 s | bit-identical |
| `reference` (same plant code, shared bridge) | 1983 s | bit-identical |
| `fast` | 1151 s | bit-identical |
| `kernel` | 423 s | bit-identical |
| `kernel2` (default) | **53 s** | bit-identical |

All five give Ton 17.750 ns, period 232.2025 ns, Vo 1.000183 V, dither
0.7066 A, P_rev 0 W, settling 116.86 us after the handover, peak 186.19 A
and 26.80 V. Each runs 38 906 796 steps and records 1756 sections.

## 2026-10-01 (later) - the step loop and the Newton fallback in C (A96)

- **`plant_kernel.c` gains:**
  - the full-Newton fallback (dgemm and dgesv with numpy's arguments);
  - `pk_run`, the whole step loop with the bridge's per-step monitors.
- **`plant.py` gains:**
  - `KernelPlant2`, the plant whose `integrate_to` runs `pk_run`;
  - `Monitors`, the shared monitor arrays and their Python update.
- **`bridge.py`:**
  - the monitor state moves to `Monitors`, for every plant;
  - the latch actions move into `latch_fire()`;
  - a `kernel2` plant choice;
  - optional profiling (`COSIM_PROFILE`).
- **Gates:**
  - A96's step-level equivalence: 519 395 steps, every field and monitor
    identical;
  - `--quick` regression with `kernel` (the bridge refactor on the Python
    path), with `kernel2`, and with the new default: PASS;
  - **`--full` with `kernel2`:** A89 r2, A92 j100, A92 m3p and A93
    m3n_both are bit-identical, **122-128 s each**, 4 at a time;
  - **`--full` with `kernel`** (the Python-monitor path, and the C
    fallback inside `pk_step`): bit-identical, 618-622 s each;
  - `tests/test_cosim_plants.py`: a KernelPlant2 loop-and-monitors test
    is added (3 tests).
- **The default plant is now `kernel2`.**

## 2026-10-01 - the package is created (code clean-up)

| piece | taken from | how it was checked |
|---|---|---|
| `rtl/` | A93's `rtl/` (A77 → A80 → A81 → A89 → A92 → A93) | Code identical to A93's below the rewritten header comments. 36/36 unit tests. Replays (below). |
| `tb/test_scb_ctrl.py` | A93's tests | Test code identical; docstring rewritten. 36/36 pass. |
| `circuit.py` | A88's `a88_transient.py`: `Params` (trimmed to the fields the co-simulation uses, as `CircuitParams`), `topology`, `EPC2067Coss`, `fit_fig8`, `Sim` | Every function body is AST-identical to A88's; `import csv` moved to the top of the module. |
| `plant.py` | `ReferencePlant`: the bridges' `Plant` (A89-A93); `FastSim` / `FastPlant`: A94's `fast_plant.py`; `KernelSim` / `KernelPlant`: A95's `kernel_plant.py` | Every method body is AST-identical to its source. The kernel library is now built content-addressed into `tmp/cosim_kernel/`. |
| `plant_kernel.c` | A95 | Code identical; header rewritten. |
| `bridge.py` | A94's bridge | The loop is unchanged. Added: plant selection (`plant_impl`, default `kernel`); `init_run` falls back to project-relative; output path, stop time and provenance from `run.py`; gzip when the output name ends in `.gz`. |
| `run.py` | new | Runs each configuration in its own process, at most `--jobs` (default 4) at a time. |
| `presets/p24_5pct_adopted.json` | A92 n0's configuration | The adopted design. `init_run` is project-relative and the output compressed. |

**Gates (2026-10-01):**
- `scripts/cosim_regression.py --full` with the kernel plant: A89 r2,
  A92 j100, A92 m3p and A93 m3n_both, full length (388.61 us), are
  **bit-identical**.
  - That covers every section, the final registers, the step count, the
    peaks, and every recorded turn-on, low-side turn-off, low-side
    turn-on and edge.
  - Format additions only: `provenance`; for A89 r2 also the fields that
    bridges newer than A89's write.
  - 542-552 s each, 4 at a time.
- `tests/test_cosim_plants.py`: FastPlant and KernelPlant against
  ReferencePlant, 3000 steps each.

### Lineage of the controller options (summary)

| experiment | option |
|---|---|
| A77 | predictive valley turn-on, comparator trim, restarts, fixed slots |
| A80 | mode S start-up, handover, voltage loop |
| A81 | asynchronous phase-1 front end (`cfg_async`) |
| A89 | timed low side (`cfg_low_pred`, dtl corrector); leading-edge blanking (`cfg_blank`) |
| A92 | error-based correctors (`cfg_err_low`, `cfg_err_high`, targets, gain) |
| A93 | period-following slots (`cfg_slot_follow`), missed-slot guard (`cfg_slot_guard`). Not adopted: they raise the dither. |
| A97 | slots from the two-period average (`cfg_slot_avg`). Adopted, with follow and guard: the dither returns to A92's and the m3n starvation stays removed. |

### Lineage of the plant (summary)

| experiment | step |
|---|---|
| A71-A73 | the N-phase zero-start circuit |
| A86 | datasheet Coss(V) |
| A87 | reverse drop |
| A94 | FastPlant: Python overhead removed, bit-identical, 1.66 times faster |
| A95 | C kernel, bit-identical, 3.17 times faster than the original |
