# scb_ivr.cosim - co-simulation of the P24 module (the shared, current version)

The Verilog controller closes the loop around the P24 circuit model.
- The RTL in `rtl/` runs in Icarus Verilog through cocotb.
- The circuit is the plant in `plant.py`, on top of `circuit.py`.

**This is the one copy that new experiments use.** Archived experiment
folders (A77-A95) keep their own frozen copies and stay reproducible with
them. This package reproduces them bit for bit: see the regression gate
below.

## Files

| file | what it is |
|---|---|
| `rtl/scb_ctrl.v`, `rtl/scb_phase.v`, `rtl/sync2.v` | The controller. Every option is a configuration bit: 0 gives each path's original behaviour. |
| `circuit.py` | Circuit parameters (`CircuitParams`), the EPC2067 data (datasheet Coss(V), Fig. 8 reverse drop) and the implicit stepper `Sim`. |
| `plant.py` | Four plant implementations with one interface, chosen by cfg `"plant_impl"`: `"kernel2"` (default: the whole step loop in C), `"kernel"` (one C call per step), `"fast"`, `"reference"`. All are bit-identical on this machine. `Monitors` holds the bridge's per-step measurement state. |
| `plant_kernel.c` | The C kernel: one plant step, with the Coss chord iteration and the full-Newton fallback, and `pk_run`, the step loop with the bridge's monitors. It uses numpy/scipy's exact operations and is built on first use into `tmp/cosim_kernel/`. |
| `bridge.py` | The cocotb test that runs one co-simulation from a configuration. |
| `run.py` | Entry point and scheduler. |
| `tb/` | The RTL unit tests (`python3 src/scb_ivr/cosim/tb/run_unit.py`). |
| `presets/p24_5pct_adopted.json` | The adopted design at P24 5%, the starting configuration for new experiments. |
| `CHANGELOG.md` | Where each piece came from, and its gates. |

## Running

```
PYTHONPATH=src python3 -m scb_ivr.cosim.run path/to/cfg_a.json path/to/cfg_b.json   # at most 4 at a time
```

- **Output.** `cfg["out"]` is written next to the configuration, or into
  `--out-dir`. A name ending in `.gz` is gzip-compressed.
- **Logs.** `log_<stem>.txt` is written next to the output.
- **Builds.** Build directories go to `tmp/cosim_build/`, which is
  git-ignored.
- **Order and length.** Configurations start in the order given, so the
  decisive ones go first. `--t-end-us` stops earlier.
- **Provenance.** Every output carries:
  - the git commit, and a flag for uncommitted changes in this package;
  - the configuration's sha256;
  - the Python, numpy and scipy versions;
  - the plant implementation.

### Configuration rules

- **A key that is absent takes the value that reproduces the earlier
  experiments.** New behaviour is always opt-in.
- **Do not change defaults to adopt a design.** Copy the preset and change
  what the experiment varies.
- **`init_run`** is resolved next to the configuration first, then relative
  to the project.

## Gates after any change here

1. RTL unit tests: `python3 src/scb_ivr/cosim/tb/run_unit.py` (36 tests).
2. Plant equivalence, in the portable suite: `tests/test_cosim_plants.py`.
3. Replays against archived runs:
   - `python3 scripts/cosim_regression.py --quick` (to 100 us, under 1
     min);
   - `--full` (4 complete runs, about 2 min).
   - `--plant X` tests another plant.
   - Both must report `PASS`.

## Speed (this machine: 4 performance and 6 efficiency cores)

A full run (388.61 us):

| plant | time |
|---|---|
| original | about 24 min alone; 70-73 min in batches of 8-10 |
| `fast` | about 14 min alone |
| `kernel` | about 9 min, 4 at a time |
| `kernel2` (default) | **about 2 min, 4 at a time** |

Run at most 4 at a time.
