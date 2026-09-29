# A77 - Verilog controller for one P24 module, co-simulated with the Python plant

- **Design:** `DESIGN.md`.
- **Declared runs:** `BOUNDARY.md`.
- **Results:** `RESULTS.md`.

## Files

| path | what it is |
|---|---|
| `rtl/sync2.v` | 2-flip-flop synchroniser for the asynchronous comparator outputs |
| `rtl/scb_phase.v` | one phase's state machine (HIGH -> DOWN -> LOW -> UP), its timers, the predictive turn-on correction and the comparator trim |
| `rtl/scb_ctrl.v` | top level: N phases, the shared time base, and phase 1's reference time `t_ref` that sets the other phases' slots |
| `tb/test_scb_ctrl.py`, `tb/run_unit.py` | cocotb unit tests of the controller alone, one design requirement per test |
| `cosim/plant_a76.py` | byte-identical copy of A76's `a76_transient.py`; the bridge uses only its `Params` and `Sim` (the circuit) |
| `cosim/test_cosim.py`, `cosim/run_cosim.py` | the co-simulation bridge (cocotb) and its runner |
| `cosim/cfg_*.json` | one file per declared case |
| `synth/stat_scb_ctrl.txt` | Yosys cell statistics |
| `a77_analyze.py` | steady-state comparison with A76 run 1 |

## How time works in the controller

- **Clock and LSB.** At 250 MHz, one clock is 4 ns. It is split into 32
  delay-line steps, so 1 LSB = 125 ps. All times inside the controller are
  counts of LSB.
- **Windows.** At each clock edge the controller handles the next 4 ns
  window.
  - A timed edge (the end of Ton, a slot, a predictive turn-on) falling
    inside the window is sent out with a 5-bit fine code, and the delay line
    places it that many LSB into the window.
  - An edge triggered by a comparator is sent at the window start. A
    comparator change needs 1-2 clocks to pass the synchroniser, so these
    edges are 4-8 ns late by construction. Timed, self-corrected edges are
    therefore used for the latency-critical instants.

## Running (OSS CAD Suite unpacked in `~/tools`, cocotb in the project Python)

```
export PATH="$HOME/tools/oss-cad-suite/bin:$PATH"
python3 tb/run_unit.py                     # unit tests
yosys -p "read_verilog rtl/sync2.v rtl/scb_phase.v rtl/scb_ctrl.v; synth -top scb_ctrl; check -assert; stat"
cd cosim && zsh run_a77_cosim.sh c1_base_250mhz_itgt2p5 c2_counter_125mhz_itgt2p5
cd .. && python3 a77_analyze.py
```

Every Verilog file starts with `` `timescale 1ns/1ps``. Without it, Icarus
simulates in 1 s units, and a 4 ns clock cannot be represented.
