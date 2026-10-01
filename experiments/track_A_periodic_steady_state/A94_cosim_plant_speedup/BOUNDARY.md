# A94 - a faster co-simulation plant that reproduces the old one bit for bit (BOUNDARY)

Track A, infrastructure. Written before any code or run.

## 1. Question

A co-simulation run (zero start to 388.61 us, 38.9 million plant steps of
10 ps) takes about 24 min alone and 70-80 min when 8-10 run together. This
machine has 4 performance and 6 efficiency cores.

A 3 us profile of A93's bridge (300k steps, 68.6 s under the profiler)
gives:
- **the plant's stepping is about 99% of the time;** cocotb and the RTL
  are negligible;
- **scipy's `lu_solve` wrapper takes 25.3 s.** That is input checks and
  array conversions around one LAPACK `getrs` call, about 3 calls per
  step;
- **the Coss lookup `q()` takes 11.0 s:** np.abs, np.interp, np.where and
  np.sign on 8 values;
- `_nonlinear` itself takes 10.5 s, `_advance` and `vds` about 8 s, and
  `vin_at` 1.9 s (13 calls per step).

**Can the same arithmetic run without that overhead, so that every
earlier result stays exactly reproducible?**

## 2. Rule: bit-identical, nothing old modified

- **New code only.**
  - `fast_plant.py` holds `FastSim`, a subclass of A88's `Sim`, imported
    read-only, and `FastPlant`, a copy of the bridges' `Plant`.
  - A88's `a88_transient.py`, the earlier bridges and all earlier
    experiments are not modified.
  - Earlier experiments keep their own plant. Later experiments may use
    the fast one.
- **Same arithmetic.**
  - Every floating-point operation keeps its operands, order and array
    layout.
  - BLAS and LAPACK are called with the same arrays: the same `@`
    expressions, including the transposed views, and scipy's own `getrs`,
    as `lu_solve` calls it.
  - Element-wise operations (IEEE, correctly rounded) may be vectorised or
    reordered between elements, never within one.
  - Only the Python overhead goes: wrappers, repeated evaluation, dict
    lookups and per-switch loops.
- **Same failure behaviour.** Non-finite right-hand sides still raise, as
  `lu_solve`'s check does.

## 3. Gates

1. **Step level.** FastPlant and the original Plant are driven side by
   side, with random gate sequences, random step sizes at window ends,
   both plant options on (Coss(V), reverse drop), and the input ramp.
   - The test runs at least 200k steps, from several random states.
   - The state y, t, diode flags, reverse energy and time, peak Vds and
     peak current must be equal bit for bit at every step.
2. **Full co-simulation replays.** A copy of A93's bridge with FastPlant
   replays stored runs, which must be bit-identical by A89's gate(): all
   sections, registers, steps and peaks.
   - A89 r2 (the adopted baseline);
   - A92 j100 (the jitter RNG path);
   - A93 m3n_both (the newest RTL and the 826 A transient path). A93's
     g1 and A92 m3n are the alternative if needed.
3. **Speed.** The wall time of the replays alone and in parallel is
   reported against the originals.

If any gate fails, the fast plant is not used, and the difference is
reported.

## 4. Does not decide

Any physics. This step changes how fast the same numbers are computed,
nothing else.
