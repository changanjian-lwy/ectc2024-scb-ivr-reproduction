# A95 - the co-simulation plant step in C, bit-identical (RESULTS)

Track A, infrastructure.

**There is no separate BOUNDARY.** The code was written and gated with
A94's criteria, which were fixed before any A94 code or run (A94
BOUNDARY Sections 2-3: same arithmetic, nothing old modified,
bit-identical step-level and replay gates). This note is written after
those gates.

**Records:**
- `plant_kernel.c` and `kernel_plant.py`;
- `a95_step_equivalence.py` / `.json` (gate 1).

The kernel now lives in the shared co-simulation package
(`src/scb_ivr/cosim/`). There it is the default plant, and the full
replays are run (gate 2; see the package CHANGELOG).

## 0. Verdict

1. **One plant step is done by a single C call**, with the same
   floating-point operations as numpy and scipy:
   - the linear solve, and A86's nonlinear-Coss chord iteration, which
     takes most of the time;
   - a chord that does not converge in 8 iterations (0.3% of steps in
     steady state, 2-6% during the input ramp) is redone in Python by
     A94's code, which takes A88's full-Newton fallback.
2. **Bit-identical to the original plant over 500 000 steps.**
   - The cases: the zero start with the input ramp, and three steady
     cases from an A92 n0 section (two of 100 000 steps, one of 200 000).
   - Compared after every step: the state, time, diode flags, Euler
     counter, reverse energy and time, peak Vds, peak current and every
     V_DS.
3. **Speed.**
   - Plant alone: 4.2-5.0 times the original (A94: 1.8-2.0).
   - Co-simulation alone, A89 r2 configuration to 60 us: **66.0 s against
     209.2 s, 3.17 times** (A94: 126.3 s). The 60 sections are identical
     to the original run's.

## 1. How the arithmetic is kept

Three checks were made before writing the kernel.

| check | result |
|---|---|
| Accelerate's `cblas_dgemv$NEWLAPACK$ILP64`, the routine numpy links, called directly with numpy's arguments (12×12, 8×12, and the transposed view r.T) | equal to numpy's `@` in 20 000 of 20 000 random cases per shape |
| scipy's `getrs` | it is Accelerate's `dgetrs$NEWLAPACK`. The kernel calls the same routine with scipy's Fortran-ordered LU and 1-based pivots. |
| numpy's compiled `interp` on the 40 001-point Coss table | equal to `fma(slope, x - xp[j], fp[j])` in 100% of 2.6 million points; only 98.9% without the FMA. **numpy's build contracts this expression**, so the kernel uses fma() there and nothing else. |

Other details:
- Everything else is one IEEE operation at a time, compiled with
  `-ffp-contract=off -fno-fast-math`.
- np.sign follows numpy: sign(-0.0) = +0.0, and NaN stays NaN.
- The finiteness check that scipy's `lu_solve` makes before each solve is
  kept. A non-finite right-hand side raises ValueError, as before.

## 2. Gate 1 (`a95_step_equivalence.json`)

| case | steps | identical | steps redone in Python | plant speed-up against the original |
|---|---:|---|---:|---:|
| ramp (zero start, t = 0) | 100 000 | **yes** | 1966 | 4.18 |
| steady, seed 2 | 100 000 | **yes** | 316 | 5.00 |
| steady, seed 3 | 100 000 | **yes** | 321 | 5.03 |
| steady, seed 4 | 200 000 | **yes** | 629 | 5.05 |

## 3. What is left

A profile of the co-simulation with the kernel, over the first 10 us
(start-up):
- the Python redo of non-converged chords is about a third of the time.
  Most of it falls in the input ramp, where 6% of steps are redone;
- the remainder is Python bookkeeping around the kernel call: topology
  look-up, the diode check, V_DS, records and the bridge's per-step
  checks.

Two possible next steps, each to be gated the same way:
- the full-Newton fallback in C (this needs numpy's `linalg.solve` path
  reproduced);
- the whole `_advance` and the bridge's per-step checks in C.

## 4. Limits

- **Machine-specific.** The bit identity is for this machine's
  numpy/scipy builds (Accelerate). The kernel builds only on macOS with
  Accelerate. Elsewhere, use `plant_impl` `fast` or `reference`.
- **Speed is measured on the start-up interval.** Mode P has fewer redone
  steps, so it should be at least as fast.
