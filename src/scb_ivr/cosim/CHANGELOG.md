# scb_ivr.cosim - changelog

History lives here and in the experiments' BOUNDARY/RESULTS, not in the
code. Each entry names its source and the gate that showed it changes no
result.

## 2026-10-02 (A109) - a valley trim for the slotted phases

Source: A108 RESULTS 0.3. The slotted phases' turn-offs had no
correction from their own current, so a lagging ladder left their
valleys positive. C01 found the same gap for slave modules.

- **`rtl/scb_phase.v`:**
  - inputs `cfg_slot_trim` and `cfg_st_smax`; output `sofs`, a signed
    offset added to a slotted phase's slot in mode P;
  - each residual-current report (r_valid) at a slot turn-off moves it
    later (r_below 0) or earlier, by a step that doubles while decisions
    agree (up to cfg_st_smax), as A100;
  - |sofs| ≤ 1024 LSB;
  - a master's phase 1 is not affected.
- **`rtl/scb_ctrl.v`:** the inputs passed to every phase; output
  `slot_ofs`.
- **`rtl/scb_multi.v`:** regenerated.
- **`bridge.py`:** cfg keys `slot_trim` (default 0) and `st_smax`.
  - With `slot_trim`, the residual-current sign is reported at every
    low-side turn-off.
  - `slot_ofs_final_lsb` is recorded.
- **Gates:**
  - RTL unit tests 53 of 53 (new: `slot_trim_adaptive_step`,
    `slot_trim_moves_the_slot`, `slot_trim_not_phase1`,
    `slot_trim_not_in_mode_s`);
  - synthesis `check -assert` clean: SLAVE 0, 47 914 cells; SLAVE 1,
    42 072;
  - wrapper and matrix tests;
  - `--full` regression PASS;
  - with the default, A105 i2_s_p62 and C02 m4_n0 rerun: every record
    identical except `wall_s` and `provenance`.

## 2026-10-02 (C02, track C) - slots referenced to phase 1's low-side turn-off; shared interleave statistics

Source: C01 RESULTS Section 2. Phase 1 of every module sat one valley
delay (9.44 ns) early, so the 16-phase interleave was not uniform.

- **`rtl/scb_ctrl.v`:**
  - input `cfg_slot_lo`: in mode P with following slots, the slots of
    phases 2..N are t_lo1 + (k − 1) T/N instead of t_ref + (k − 1) T/N.
    Configured slots stay on t_ref.
  - output `t_lo1`: phase 1's last low-side turn-off.
  - A phase still learns of a new cycle from t_ref, so the slot must
    lie after it: T/N − dt_pred > ~2 windows.
- **`rtl/scb_phase.v`:** output `t_lo_q` (its t_lo).
- **`rtl/scb_multi.v`:** regenerated.
- **`bridge.py`:** cfg key `slot_lo` (default 0). With it, the slaves'
  slot base and reference id are the master's t_lo1.
- **`matrix.py`:** `phase_waveform`, `ref_turnons`, `lsoff_after` and
  `output_ripple`, C01's interleave statistics as shared functions. C01's
  own script stays as the record.
- **Gates:**
  - RTL unit tests 49 of 49 (new: `follow_slots_from_phase1_low_off`,
    `slot_lo_keeps_configured_slots_at_t_ref`);
  - synthesis `check -assert` clean: SLAVE = 0, 46 443 cells; SLAVE = 1,
    40 127;
  - `--full` regression PASS;
  - `tests/test_cosim_matrix.py`: the shared interleave statistics equal
    C01's (ripple in four placements, low-side turn-off times);
  - with the default (`slot_lo` 0), A105 i2_s_p62 (one module, to
    600 µs) and C01 m4_n0 (four modules, to 500 µs) rerun: every record
    identical except `wall_s` and `provenance`.

## 2026-10-02 (C2, C3, track C) - multi-module: slave modules and the M-module system

- **`rtl/scb_ctrl.v`:**
  - inputs `cfg_ext_ton` and `ext_ton`: in mode P, Ton is ext_ton (the
    master's, broadcast);
  - parameter `SLAVE` (default 0) with inputs `ext_slot` and `ext_ref`:
    a slave's phase 1 is a slotted phase like phases 2..N, its low-side
    turn-off at ext_slot once per reference ext_ref. It resets LOW, and
    phase 1's front end and timed turn-off are off for it.
- **`rtl/gen_multi.py` → `rtl/scb_multi.v` (generated):** M instances,
  0 the master and 1..M-1 slaves. Every port except clk and rst is M
  times as wide.
- **`run.py`:** cfg `modules` > 1 builds `scb_multi` with M.
- **`bridge.py`:**
  - `MultiCtl`: module m's slice of the wrapper's signals; combined
    writes through a shared cache.
  - `cosim_multi`: M `ModuleSim`s, each the single-module plant with its
    own Co and load, so the system has M Co and the load / M.
    - Output nodes joined after every window by charge conservation; the
      largest and mean differences are recorded.
    - The master's Ton is broadcast.
    - Slave m's phase-1 slot is t_ref + m T / (M N) after each master
      turn-on (T: the master's last period, or the mean of its last two).
  - cfg keys `modules`, `module_circuit` (per-module circuit values); a
    load step's i_a is the system's.
  - The new inputs are set to 0 for a single module.
- **Gates:**
  - RTL unit tests 47 of 47 (new: `external_ton`);
  - synthesis `check -assert` clean: SLAVE = 0, 46 566 cells (A104
    46 468); SLAVE = 1, 40 447;
  - `tests/test_cosim_wrapper.py`: the wrapper regenerates identically;
  - M = 1: `--full` regression and the four feature-rich reruns (C1's)
    identical;
  - M = 2 smoke run (A105 I2 to 120 µs): no overlap; both modules in
    mode P at 72 µs; Vo 1.0000 V; equal currents; join difference ≤ 50 µV.

## 2026-10-02 (C1, track C) - the bridge per module, for multi-module runs

- **`bridge.py`:** restructured with no change in behaviour.
  - One module's plant, controller-side analog functions, measurements
    and records are a `ModuleSim`, with the window steps `read_rising`,
    `write_falling`, `run_window` and `sample`.
  - The controller's signals go through `Ctl` (with one module, the DUT).
  - `load_cfg` and `make_params` are shared.
  - Every operation keeps its order.
- **Gates:**
  - `--full` regression PASS;
  - A105 i2_s_p62 (timed turn-off, PI, load step), A106 pi100_p48_1us
    (line step), A102 e125_5v (branch enable) and A107 cs8p7_n0 (cfg
    `circuit`) rerun to their ends: every record identical except
    `wall_s` and `provenance`.

## 2026-10-02 (A107) - circuit values as scenario inputs; the shared standard matrix

- **`bridge.py`:** cfg key `circuit` {name: value, SI}.
  - Any of `CIRCUIT_KEYS` (vin, L, R, c_high, c_low, cs, co, r_load,
    i_load, g_on) replaces the init run's value.
  - Other names are refused. Structural values (n, load kind) stay out.
  - One mechanism for every circuit-value scenario, instead of a key per
    value.
- **`matrix.py` (new):** the standard matrix as one definition: rows,
  configurations from a step-free base, `window_stats`, `step_stats`.
  - It replaces copies in experiment folders. A105's `matrix_stats.py`
    stays as the record.
- **Gates:**
  - `--full` regression PASS;
  - `circuit: {cs: 3e-6}` (the default) gives sections and steps
    identical to no override (A105 i2_n0 to 30 µs);
  - `tests/test_cosim_matrix.py`: the module regenerates A105's and
    A106's configurations exactly, and its statistics equal A105's and
    A106's.

## 2026-10-02 (A106) - input (line) step

- **`circuit.py`:** `vin_step`, `t_vstep`, `t_vslew`. `vin_at` adds
  vin_step × min((t − t_vstep)/t_vslew, 1) from t_vstep (at once if the
  slew is 0); nothing without a step.
- **`plant_kernel.c`, `plant.py`:** the same in the C `vin_at`; the run
  struct and `_Run` gain the three fields at the end.
- **`bridge.py`:** cfg key `line_step` {"t_us", "dv", "slew_us"}.
- **Gates:**
  - `--full` regression PASS;
  - `tests/test_cosim_plants.py` `CosimPlantLineStep`: −4.8 V over 10 ns
    inside the lockstep window. Fast, Kernel and Kernel2 (loop and
    monitors) are bit-identical with Reference.

## 2026-10-02 (A104) - proportional term in the voltage loop

- **`rtl/scb_ctrl.v`:** input `cfg_kp` (parameter KPW = 24, FRAC = 16
  fractional bits).
  - At each ADC sample in mode P with the loop on, p_term = kp × e is
    held.
  - Ton = round(ton_acc + p_term), clamped to [ton_min, ton_max].
  - With cfg_kp = 0, Ton is A79's round(ton_acc).
- **`bridge.py`:** cfg key `kp_ns_per_v` (default 0), in the same units as
  `ki_ns_per_v`.
- **Gates:**
  - RTL unit tests 46 of 46 (2 new: `voltage_loop_proportional`,
    `voltage_loop_pi`);
  - synthesis `check -assert` clean, 46 468 cells (A100: 43 924);
  - `--full` regression PASS.

## 2026-10-02 (A103) - start-up sequence timing

- **`bridge.py`:** cfg keys `t_load_us` and `t_hand_us` override the init
  run's load connection and handover request times (default: the init
  run's, 88.61 µs each).
- **Gate:** `--full` regression PASS.
- **RTL and plant unchanged.**

## 2026-10-02 (A102) - branch enable time and per-branch precharge

- **`plant.py`:** `aux_armed` (default all True). A disarmed branch
  ignores its low side's edges, so its switch stays open; once armed it
  starts at its next low-side turn-off. Python-side only (`_aux_gate`),
  shared by all four plants; the C kernel is unchanged.
- **`bridge.py`:** cfg `aux` keys `t_en_us` (default 0: armed from the
  start, as A101) and `vm0_v` as one value or one per branch. With
  `t_en_us` > 0 the branches start disarmed and open, and are armed at
  the first window at or after `t_en_us`. `aux_params` records `vm0_v`
  as a list per branch, `t_en_us` and `t_armed_s`.
- **Gates:**
  - `--full` regression PASS (format additions as before);
  - `tests/test_cosim_plants.py`: `CosimPlantAuxEnable` (disarmed for
    150 ns, then armed; per-branch precharges): FastPlant and KernelPlant
    bit-identical with ReferencePlant, and no branch current while
    disarmed;
  - A101's `dz_vz0` and `p125` rerun to 100 µs: every section equal to
    the archived runs.
- **RTL unchanged.**

## 2026-10-02 (A101) - auxiliary commutation branches

- **`circuit.py`:** `aux_phases`, `aux_l`, `aux_r`, `aux_c`, `aux_vm0`.
  - Per listed phase, a node m_k with Cm to ground (after "out") and a
    branch current (after the phase currents) through Lr from m_k into
    x_k while its bidirectional switch conducts.
  - The switch states follow the 2N switches in `conducting`. An open
    branch is uncoupled, with di/dt = 0.
  - Without branches every matrix is as before.
- **`plant.py`, `plant_kernel.c`:** the same in all four plants.
  - The switch is commanded with its phase's low side complemented.
  - It opens at the step where its current reaches or crosses zero after
    the open-command (current set to 0, Euler restart).
  - Per branch: int i² dt and the current extremes.
  - The peak phase current counts the phase currents only.
  - Monitors' `vmin_zero`: the high side's minimum stops at its first
    V_DS ≤ 0.
  - The C run struct gains its fields at the end.
- **`bridge.py`:**
  - cfg key `aux`;
  - Cm voltages and branch records in the sections;
  - `highoffs_last` (phase and branch currents at every high-side
    turn-off) in every run, a format addition.
- **Gates:**
  - `--full` regression PASS (`highoffs_last` listed as a format
    addition);
  - `tests/test_cosim_plants.py`: 3 new tests with branches on every
    phase. ReferencePlant, FastPlant, KernelPlant and KernelPlant2 are
    bit-identical, including the zero-current openings.
- **RTL unchanged.**
- **Later the same day:** `valley_zero` defaults to 0. With 1, the
  turn-off currents of phases 2-4 became unstable in A101 (z075); with
  the plain valley measurement the same design is stable (dz_vz0). All
  A101 configurations set the key explicitly.

## 2026-10-01 (night, A100) - adaptive dlo step and Ton feedforward

- **`rtl/scb_phase.v`, `rtl/scb_ctrl.v`:**
  - `cfg_lo_adm` / `cfg_lo_smax`: dlo's step doubles while consecutive
    decisions agree, up to the cap, and returns to 1 when they differ
    (Jayant's adaptive delta modulation).
  - `cfg_lo_ff` / `cfg_lo_kff`: dlo moves by kff times every change of
    ton.
  - With both at 0, dlo's update is A99's ±1 with a floor at 0.
- **`bridge.py`:** cfg keys `lo_adm`, `lo_smax`, `lo_ff`, `lo_kff`.
- **`tb/`:** 2 new tests. **44 of 44 pass.**
- **Gates:**
  - `--full` regression PASS;
  - A99 n0 replayed bit-identically;
  - synthesis 0 problems, 43 924 cells.
- **A100's result:** ADM32 (`lo_adm` 1, `lo_smax` 32) tracks ±25 and
  ±62.5 A steps within 1.7 A.
- **Recommended, not yet in the preset**, pending the trade-off review
  (`reports/TRADEOFF_SCORECARD.md`).

## 2026-10-01 (night, A100) - load step and record length

- **`circuit.py`, `plant_kernel.c`, `plant.py`:** a load current step
  (`i_step` from `t_step` on), on top of the load, in the source term.
  - No step: a + 0.0, so nothing changes.
  - The C run struct gains two doubles at its end, so no other field
    moves.
- **`bridge.py`:** cfg keys `load_step` {"t_us", "i_a"} and
  `records_last` (default 1000).
- **Gates:**
  - `--full` regression PASS;
  - `tests/test_cosim_plants.py` passed.

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
