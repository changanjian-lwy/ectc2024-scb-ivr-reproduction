# A233 - a faster low-side learner on phase 1 (BOUNDARY)
Method: cosim (cfg only; code as at 63d7c8b).
Track A. Written and committed before the runs. Looked at beforehand: A225's item 2 records (phase 1's valley and its
low-side reports after the step), A223's binding-row record, A223 / A224's account of the ring.
Decision it changes: phase 1's lo_smax in the final configuration (64 = 2 ns per decision), and with it whether item 2's
40 us hold-off after the handover can go and how much margin the binding row (S75 125 C +4.8 V / 1 us, 192.9 A on the
final controller) gains.
Cheaper check done first: the records. In A225 run_a_S75h_d2.json every phase-1 low-side report from 4 to 22 us after
the entry is "early" (the timed edge comes before the current reaches -15.6 A, no error measured), one per period, and
the valley sits at +2..+7 A meanwhile: the step's rail jump (12.3 -> 16.2 V) raises phase 1's peak, its low-side
interval has to grow by tens of ns, and the learner moves at most 64 LSB = 2 ns per decision. The same step at 500 us
holds the valley near 0 A for ~14 us (A223 run_k_S75h_g25.json). D63 was not used: it has no handover, and its timed
mode misses the rising-step period stretch (scb-map's blind spots). Budget: 24 runs, about 2.5 h at 10 jobs.

## 1. What and why
- A223 named the same 2 ns limit as the integrator behind the large-load-step ring, and A224's D63 study found that
  holding the valley (F1 / F2) doubled the load-step dip: a faster learner can cost on load steps what it gains on line
  steps. So the rows cover both sides.
- Arms: lo_smax 128 (4 ns) and 255 (~8 ns; cfg_lo_smax is 8 bits); everything else the final configuration.
- Rows (one module, 25 C unless named), each against its record at lo_smax 64: item 2 (S75 125 C +4.8 V / 1 us at 2 /
  10 / 20 us after the entry; S75 25 C at 20 us) - A225; the binding row k_S75h, k_N0 (+62.5 A), w5_N0 / w20_N0 /
  w5_N75 (re-applications), z_N0_10 at t0 (skipping) - A229 b; l_N0_p48 / l_N0_m80 - A228 h. The A225 references ran
  without kd_band and the N0 references without hand_lead: both inert on these rows (Ton register >= 21.5 ns; no request
  at 25 C full load), A229 / A230.
- Not tested: other boards / temperatures for the load rows, four modules, the falling step (A232 runs it at 64).

## 2. Criteria (per arm)
- every row: completes, no overlap or shoot-through, V_DS <= 40 V.
- m1 (item 2): post-step peak <= 200 A on all four rows.
- m2 (binding row): post-step peak <= reference + 0.5 A.
- m3: k_N0 post-step peak <= reference + 1 A and |Vo extreme| <= |reference| + 1 mV; w rows whole-run peak <= 200 A, Vo
  within 1 % over the last 20 us, |Vo extreme| <= |reference| + 2 mV.
- m4 (line rows): post-step peak <= reference + 1 A and |Vo extreme| <= |reference| + 1 mV.
- m5 (z_N0_10, one run): A228's q1 run test and true valleys within A228's d0 means +-1 A (-17.16 / -12.60 A).

## 3. Predictions (not criteria)
- s128: item 2 peaks 5-10 A lower (200-205 A), binding row 3-6 A lower; s255: item 2 <= 200 A, binding row 6-12 A lower.
- k_N0's dip 1-3 mV deeper in both arms (A224's D63 finding), so m3 at risk; line rows within 1 A; z_N0_10 within band.

## 4. Decision rule
- The smaller lo_smax passing every criterion enters the final configuration; with m1 the hold-off after the handover
  is dropped (item 2 closes on the tested boards).
- None passes: lo_smax stays 64; the record says which side (line or load) each arm cost.
