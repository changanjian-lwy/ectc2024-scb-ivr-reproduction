# C02 - the uniform interleave: slots referenced to phase 1's low-side turn-off (BOUNDARY)

Track C. **Written before any C02 run.** It corrects the deviation
flagged in C01 (RESULTS Section 2): phase 1 of every module sits one
valley delay early.

## 1. Question

**The factor:** reference the slots to phase 1's low-side turn-off
instead of its high-side turn-on. cfg `slot_lo` = 1, an opt-in RTL
setting; the default keeps A93/A97's placement.

Does this give uniform low-side turn-offs (T/N in one module, T/(M·N) in
four modules) and the ripple cancellation C01's re-placement predicted?
And does it leave everything else unchanged:
- soft switching;
- sharing;
- steps;
- start-up?

## 2. The change (P24 consistency)

| point | before (A93/A97, C01) | C02 (`slot_lo` = 1) | P24 |
|---|---|---|---|
| phase k's slot (k = 2-4), mode P with following slots | t_ref + (k − 1) T/N, t_ref = phase 1's high-side turn-on | t_lo1 + (k − 1) T/N, t_lo1 = phase 1's low-side turn-off | "interleaved"; uniform is the natural reading (Roberts' SCB: phases T/N apart). This makes it uniform in low-side turn-off terms |
| slave m's phase-1 slot | master's t_ref + m T/(M N) | master's t_lo1 + m T/(M N) (also the reference id) | "interleaved phases and modules" |
| mode S, and before the period is known | configured slots from t_ref | unchanged | - |

**RTL** (`scb_ctrl.v`, `scb_phase.v`):
- New: input `cfg_slot_lo`; output `t_lo1`, phase 1's last low-side
  turn-off.
- A phase still learns of a new cycle from t_ref. So the slot must lie
  after t_ref is seen: T/N − dt_pred > ~2 windows (8 ns).
  - Full load: 58 − 9.4 = 48.6 ns.
  - A passed slot fires late and is counted in `late_fires`.

**Bridge:** with `slot_lo`, the slaves' slot base and reference id are
the master's t_lo1.

**Gates, before the runs:**
- RTL unit tests 49 of 49 (new: `follow_slots_from_phase1_low_off`,
  `slot_lo_keeps_configured_slots_at_t_ref`);
- synthesis `check -assert` clean (SLAVE 0: 46 443 cells, SLAVE 1:
  40 127);
- `--full` regression;
- A105 i2_s_p62 and C01 m4_n0 rerun with the default, identical.

## 3. Runs (the physical model of A105 / C01 unchanged; only `slot_lo`)

| run | from | to |
|---|---|---|
| s1_n0, s1_j30, s1_s_m62, s1_s_p62 | A105 i2 (one module) | 500 / 500 / 600 / 600 µs |
| m4_n0, m4_L5, m4_j30, m4_s_m250, m4_s_p250 | C01 (four modules) | 500 / 500 / 500 / 600 / 600 µs |

Part A (one module) runs first. Part B only if Part A keeps the module's
soft switching.

## 4. Registered predictions and criteria (last 200 periods; before the step for step runs)

**A. One module (vs A105 i2):**
1. **Identical to A105 until the following slots start.** The sections
   are equal up to the handover at 72 µs; the change acts only in mode P
   with the period known.
2. **The four low-side turn-offs are T/4 apart:** each phase k at
   (k − 1) T/4 ± 0.1 ns after phase 1's (n0).
3. **The module's output current ripple** (the same piecewise-linear
   sum as C01): 100.9 A pk-pk and 29.4 A rms (C01's re-placement),
   each ±20%. A105's actual is 122.4 / 31.3 A.
4. **Soft switching unchanged:**
   - every phase's valley within ±0.5 A of A105's;
   - high-side turn-on within ±0.2 V;
   - low-side turn-on V_DS ≤ 0 (n0);
   - no overlap; peak ≤ 200 A;
   - no more late fires than A105.
5. **Vo 1.000 V ± 1 mV.** Steps within ±10% of A105's (+11.65 /
   −14.68 mV). j30's turn-off sd within A105's ×(1 ± 0.3).

**B. Four modules (vs C01):**
1. **The 16 low-side turn-offs are T/16 apart:** every gap 14.50 ±
   0.1 ns (m4_n0; C01: 4.4-23.9 ns).
2. **System output current ripple (m4_n0):** 31.3 A pk-pk and 6.6 A rms
   (C01's re-placement), each ±30%. C01 actual: 162.8 / 45.9 A.
   - m4_L5: 69.7 A pk-pk, 9.0 A rms, ±30%.
3. **Everything else as C01:**
   - locked periods (0.1 ns);
   - normalised currents within ±1 A of C01's;
   - valleys within ±0.5 A of C01's;
   - steps within ±10% of C01's (+11.4 / −14.6 mV);
   - start-up ≤ 1.05 V;
   - no overlap; peak ≤ 200 A; join ≤ 0.1 mV;
   - no more late fires than C01.

**What would falsify the correction:**
- a late fire in steady state;
- a phase losing zero-voltage turn-on;
- the ripple not falling.

The last would mean the waveforms change when moved, so C01's
re-placement was wrong.

## 5. What stays assumed

As C01 (BOUNDARY Section 5):
- identical controllers;
- one output node;
- an ideal shared input;
- 25 C;
- Co inherited.
