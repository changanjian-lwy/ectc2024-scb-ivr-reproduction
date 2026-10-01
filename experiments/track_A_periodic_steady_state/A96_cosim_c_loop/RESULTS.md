# A96 - the co-simulation step loop and the full-Newton fallback in C, bit-identical (RESULTS)

Track A, infrastructure, part of the code clean-up.

**There is no separate BOUNDARY.** The gates are A94's criteria: the same
arithmetic, nothing archived modified, bit-identical at step level and in
full replays.

**Records:** `a96_loop_equivalence.py` / `.json`. The code is in the
shared package `src/scb_ivr/cosim/`: `plant_kernel.c`, and `plant.py`
(`KernelPlant2`, `Monitors`).

## 0. Verdict

1. **KernelPlant2 runs the step loop in C.** In C it does:
   - FastPlant's `_advance`: A73's diode check, reverse-conduction energy,
     peak V_DS and current, diode flags, the Euler counter;
   - the bridge's per-step monitors: the low sides' zero-crossing TDC and
     the high sides' valley tracking;
   - the phase-1 latch test.

   One call runs until the target time. It comes back to Python only for:
   - a partial step (h ≠ 10 ps, at edges and window ends);
   - a missing topology entry, which Python builds and registers once;
   - the latch firing, for the edges Python schedules.
2. **The full-Newton fallback is in C too.** The profile of A95 showed
   that 5.3% of steps up to 95 us (mostly the input ramp) failed the chord
   iteration and were redone in Python, and that this took about 80% of
   the time. It reproduces numpy:
   - w = n·c(v1) − clin, with numpy's FMA in interp;
   - (r.T · w) @ r through `cblas_dgemm$NEWLAPACK$ILP64` (RowMajor, Trans
     on the Fortran-ordered r.T·w, NoTrans on r);
   - np.linalg.solve through `dgesv$NEWLAPACK$ILP64` on Fortran-ordered
     copies.
   - All three were checked equal to numpy in 20 000 of 20 000 random cases
     each (the layout, the product, and the solve with the circuit's own
     matrices).
3. **Bit-identical at step level.**
   - Three cases (zero start with the input ramp, and two A92 n0 sections),
     519 395 steps.
   - After every interval between gate edges: the state, time, diode
     flags, Euler counter, steps, reverse energy and time, peak V_DS and
     current, every V_DS and every monitor array.
   - The latch fired at the same steps: 2, 33 and 34 times.
4. **39-43 times faster than the reference plant** stepped in Python with
   Python monitors (A95's kernel: about 5 times).
5. **Full replays:** see the package CHANGELOG (gate 2).

## 1. The bridge change it needed (in the shared bridge only)

The bridge's monitor state used to be lists with None. It is now a
`Monitors` object of flag and value arrays, shared with the C loop:
- the TDC's turn-off time, crossing time and previous V_DS;
- the valley's minimum and its time.

Every read converts back to a Python float, so the numbers and the output
format are unchanged. The latch actions moved into a function used by both
paths.

**Check.** `scripts/cosim_regression.py --quick` with the kernel plant
(the Python-monitor path) passes: every section to 100 us is identical in
all four archived cases.

## 2. Limits

- The equivalence is for this machine's numpy/scipy (Accelerate). The C
  code needs macOS Accelerate.
- Partial steps are still done in Python, about 1.2 per 4 ns window. They
  could move to C with getrf for arbitrary h, if needed.
