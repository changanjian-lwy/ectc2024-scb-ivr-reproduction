# A80 - the full P24 module controller in Verilog

- **Declared runs:** `BOUNDARY.md`.
- **Results:** `RESULTS.md`.
- **Base design:** A77's `DESIGN.md`, unchanged in principle.

## What changed from A77 (A77's files are not modified)

| file | change |
|---|---|
| `rtl/scb_phase.v` | **Mode S** (fixed start-up timing). **Chained edges:** a high-side turn-off and the low-side turn-on one dead time later are emitted in the same window when both fall in it; the 2.15 ns dead time is shorter than a 4 ns clock. **Ton input:** Ton now comes in as an input. `on_how` has a fifth value, 4 = timed (mode S). |
| `rtl/scb_ctrl.v` | **Mode register:** reset into S; `hand_req` switches it to P at the next phase-1 turn-on. **Voltage loop:** a Ton accumulator with 16 fractional bits, updated from a 12-bit ADC sample of Vo taken at each phase-1 turn-on, in mode P only. |
| `rtl/sync2.v` | unchanged |
| `tb/test_scb_ctrl.py` | A77's ten tests, unchanged in mode P, plus five tests of mode S, the chained edges, the handover and the loop |
| `cosim/test_cosim.py` | A77's bridge, starting from the all-zero plant, with the input ramp, the load connection, `hand_req`, and the ADC sample |
| `cosim/plant_a79.py` | byte-identical copy of A79's `a79_transient.py` |

## Running

```
export PATH="$HOME/tools/oss-cad-suite/bin:$PATH"
python3 tb/run_unit.py
yosys -p "read_verilog rtl/sync2.v rtl/scb_phase.v rtl/scb_ctrl.v; synth -top scb_ctrl; check -assert; stat"
cd cosim && zsh run_a80_cosim.sh f0_zero_start_loop_off && cd ..
python3 a80_analyze.py
```

A full zero start (388.61 us of plant time) takes about 15 minutes of wall
time.
