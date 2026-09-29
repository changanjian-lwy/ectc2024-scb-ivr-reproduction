# A81 - asynchronous fast path for phase 1 (Verilog + behavioural front end)

- **Declared runs:** `BOUNDARY.md`.
- **Results:** `RESULTS.md`.
- **Base:** A80. A80's files are not modified.

## What changed from A80

| file | change |
|---|---|
| `rtl/scb_phase.v` | `cfg_async`, `a_valid`, `a_tlo` in, `arm` out. With `cfg_async`, phase 1 in mode P raises `arm` while LOW and ignores the synchronised comparator. On the TDC report it records `t_lo = a_tlo` and `t_on = a_tlo + dt_pred` and enters HIGH, with no gate event for those two edges. The 400 ns restart stays clocked. |
| `rtl/scb_ctrl.v` | brings out `cfg_async`, `a_valid`, `a_tlo` and `arm1` |
| `tb/test_scb_ctrl.py` | A80's 15 tests with `cfg_async` = 0, plus 3 async tests: the report records both edges without gate events, the synchronised comparator is ignored while armed, the restart stays clocked |
| `cosim/test_cosim.py` | the behavioural front end. While armed, a comparator plus latch fires at the plant step where `i1 <= threshold` and schedules SL1 off at `t + t_async + t_drv` and SH1 on `dt_pred` later. A TDC reports `t + t_async`. |

## The partition, in one sentence

The clocked controller decides **when the fast path may act and with what
settings**: it arms the path, sets the threshold trim and the delay-line
code, and keeps timing everything else. The asynchronous front end makes
the two time-critical edges without waiting for a clock.

Chiang 2009's controller works the same way, with no clock at all.
Schaef 2019's clocked logic likewise only trims an on-chip comparator
path.

## Running

```
export PATH="$HOME/tools/oss-cad-suite/bin:$PATH"
python3 tb/run_unit.py
cd cosim && zsh run_a81_cosim.sh g0_async_off_gate g1_async_on && cd ..
python3 a81_analyze.py
```
