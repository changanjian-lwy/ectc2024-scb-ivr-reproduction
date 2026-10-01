# scb_ivr.cosim - changelog

History lives here and in the experiments' BOUNDARY/RESULTS, not in the
code. Each entry names its source and the gate that showed it changes no
result.

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

### Lineage of the plant (summary)

| experiment | step |
|---|---|
| A71-A73 | the N-phase zero-start circuit |
| A86 | datasheet Coss(V) |
| A87 | reverse drop |
| A94 | FastPlant: Python overhead removed, bit-identical, 1.66 times faster |
| A95 | C kernel, bit-identical, 3.17 times faster than the original |
