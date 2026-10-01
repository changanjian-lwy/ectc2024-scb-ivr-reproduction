# A94 - a faster co-simulation plant that reproduces the old one bit for bit (RESULTS)

Track A, infrastructure. **Boundary:** `BOUNDARY.md`, written before any
code or run.

**Records:**
- `fast_plant.py`;
- `a94_step_equivalence.py` / `.json` (gate 1);
- `a94_analyze.py` / `a94_summary.json` (gates 2-3 and speed);
- `cosim/`: A94's bridge, replay configurations and replay runs, and the
  fast speed run;
- `cosim_orig/`: the original-plant speed run.
  - Its bridge is a byte copy of A93's `cosim/test_cosim.py`
    (sha256 f817818d423a3343…). It is not committed: copy it there to
    rerun.

## 0. Verdict

1. **FastPlant reproduces the original plant bit for bit.**
   - **Step level:** 300 000 steps from three starting states. Every
     quantity was equal after every step: the state vector, time, diode
     flags, Euler counter, reverse energy and time, peak Vds, peak current
     and every switch's V_DS. This includes the rare full-Newton fallback
     (1966, 316 and 321 times in the three cases).
   - **Full replays (388.61 us each):** A89 r2, A92 j100 and A93 m3n_both
     are bit-identical to the stored runs. That covers every section, the
     final registers, the step count, the peaks, and every recorded
     turn-on, low-side turn-off, low-side turn-on and edge.
   - The only differences are fields that the newer bridge writes and A89's
     did not. A89 r2's replay adds `driver`, `overlaps`, `status`,
     `first_overlap`, and `early` / `err_s` in the turn-on records.
2. **It is 1.66 times faster per run.** Alone on an idle machine, the A89
   r2 configuration to 60 us takes:
   - 209.2 s with the original plant (0.287 us/s);
   - 126.3 s with FastPlant (0.475 us/s).

   The step-level gate measured 1.8-2.0 times on the plant alone. The
   difference is the bridge's own per-step work, which is unchanged.
3. **With at most 4 runs at a time, a full run takes about 16 min.**
   - Three replays in parallel took 944-971 s each.
   - The references took 1748 s (A89 r2, 4 in parallel), 4373 s (A92 j100,
     8 runs plus 2 orbit computations) and 4173 s (A93 m3n_both, 10 runs
     plus 1).
4. **Nothing earlier was modified.** A88's `a88_transient.py`, A89-A93's
   bridges and all stored runs are untouched. Later experiments may use
   `fast_plant.py`.

## 1. What changed (Python overhead only)

| place | original | FastPlant | why the arithmetic is the same |
|---|---|---|---|
| linear solves (3 per step) | `scipy.linalg.lu_solve` | the same LAPACK `getrs` that `lu_solve` calls, with the same arrays; the finiteness check kept | identical routine and inputs |
| Coss(V) lookup | np.abs, np.interp, np.where, np.sign | the same operations, numpy's compiled interp called directly; np.where only if some \|V\| > 40 V (never reached) | identical element-wise operations |
| source terms h·f, h·frev, n_vin·vin | recomputed every step | the same expressions, memoised per topology and value | the same expression evaluated once |
| V_DS of the 8 switches | 8 scalar calls per use, about 30 per step | one vectorised subtraction per state | element-wise IEEE, identical to the scalar one, including signed zeros |
| peak Vds, diode flags | Python lists | numpy maximum and comparisons | identical values |
| dense products (`@`), including the transposed view `r.T` | numpy (Accelerate BLAS) | unchanged | the same calls and layouts |

**A check that set the limit.** The dense 12×12 products cannot be
replaced by compiled code without changing bits. Against numpy's
Accelerate `@`, four simple summation orders matched only 2-3.5% of
random cases (sequential, column-wise, each with and without FMA). The
0/±1 incidence products matched in every case.

**So compiled kernels (Numba, C++) would give larger speed-ups only by
changing the rounding**, and with it every earlier trajectory. They are
left for a separate, statistically gated screening tool, if one is ever
needed.

## 2. Gate 1: step level (`a94_step_equivalence.json`)

| case | start | steps | identical | full-Newton fallbacks | plant speed-up |
|---|---|---:|---|---:|---:|
| ramp | zero state at t = 0, input ramp, load off | 100 000 | **yes** | 1966 | 1.81 |
| steady_seed2 | A92 n0 section at about 300 us, 48 V, load on | 100 000 | **yes** | 316 | 1.97 |
| steady_seed3 | same, another seed | 100 000 | **yes** | 321 | 2.01 |

Both plants get A93 n0's plant parameters, with datasheet Coss(V) and
Fig. 8 reverse drop. The gate sequence is a four-phase pattern (Ton, dead
times, T/4 slots) with 0.3 ns jitter, so edges fall between 10 ps steps.

## 3. Gates 2-3: full replays (`a94_summary.json`)

| replay | reference | result | wall (3 in parallel) | reference wall (its batch) |
|---|---|---|---:|---:|
| r_a89r2 | A89 r2 (adopted baseline at A89) | **bit-identical** (format additions only) | 944 s | 1748 s |
| r_a92j100 | A92 j100 (the jitter RNG path) | **bit-identical** | 970 s | 4373 s |
| r_a93m3nboth | A93 m3n_both (newest RTL, slot rules) | **bit-identical** | 971 s | 4173 s |

## 4. How runs are scheduled from now on

The machine has 4 performance cores and 6 efficiency cores.
- Batches of 8-10 runs put most runs on efficiency cores. The total
  throughput did not rise (A92: 0.71 us/s summed, against 0.89 us/s for
  A89's 4 runs), and each result arrived about twice later.
- **From now on at most 4 runs at a time, the decisive ones first.**

## 5. Limits

- The equivalence is proven for this machine's numpy/scipy build
  (Accelerate BLAS, scipy's LAPACK). Another BLAS changes the dense
  products for both plants alike. Comparisons across machines need the
  stored runs, not bit identity.
- The speed-up was measured on the start-up interval (0-60 us). Mode P
  adds the bridge's measurement work, which is the same in both versions.
