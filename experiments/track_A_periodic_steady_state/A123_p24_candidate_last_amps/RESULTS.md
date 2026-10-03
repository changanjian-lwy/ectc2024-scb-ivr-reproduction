# A123 - the candidate's last amps: Cs 4.5 µF, a 3 A floor, or a 66 kHz loop (RESULTS)

Track A, main line.

**Boundary:** `BOUNDARY.md`, committed (ee011d2) before any run.

**Records:**
- `cosim/run_*.json`, `cfg_*.json`;
- `a123_summary.json` (`a123_analyze.py`).

## 0. Verdict

**No single lever closes all three misses.** Each moves 1-11 A, about
as large as the misses themselves:

| variant | +4.8 V / 1 µs | −4.8 V / 1 µs | −8 V / 10 µs | start-up | efficiency |
|---|---|---|---|---|---|
| f6 (A118 / A119) | 206 A | 201 A | 205 A | 157 A | 88.97% |
| c45 (Cs 4.5 µF) | **195 A** | 209 A | **199 A** | 152 A | 88.96% |
| f3 (floor 3 A) | 206 A | 203 A | **200 A** | 157 A | 88.97% |
| k66 (66 kHz) | 204 A | **195 A** | **194 A** | 154 A | 88.97% |

- No overlap and no runaway in any of the 12 runs (late fires ≤ 1).
- The steady state is unchanged.

**Notes per lever:**
- **The faster ladder (4.5 µF)** cuts the rising step's peak by 11 A,
  but raises the falling one by 8 A. The 4.5 µF handover is clean
  (152 A).
- **The faster loop (66 kHz)** cuts the falling steps by 6-11 A.
- **A deeper floor** does almost nothing. Phase 1 is not what peaks.
- **D63's estimates (≤ 4 A) were in the right direction but too
  small** for c45 and k66, as registered (below its own error).

**Untested next screen:** c45 + k66 together. The two levers act on
different steps. **It runs only if the 1 MHz design is pursued:** D64
(the inductor model) finds 1 MHz is not the efficiency optimum at P24's
in-package scale, and the plan moves to 2-3 MHz (A124).
