# A232 - the fast falling step on plant V7: does item 3 survive the adopted controller? (BOUNDARY)
Method: cosim (cfg only; code as at 63d7c8b).
Track A. Written and committed before the runs. Looked at beforehand: the oracle events of existing falling-step records
(a142_oracles.check from the step on): -4.8 V / 1 us on V6 (A212 run_n_l_m48_1us.json): 3 K3 restarts, 3 NEW; -8 V /
10 us on V6 (A212) and on V7 in A223 (off, g25), A224 (kd 355) and A228 (arm h): none.
Decision it changes: whether controller item 3 (phases 2-4 lose their valley after a fast falling step: K3 restarts and
10-20 A spikes, A148 / A176 / A212) is still open on the adopted configuration, and so whether it needs a fix next.
Cheaper check done first: the existing records above; no V7 record of -4.8 V / 1 us exists. Budget: 14 runs to 620 us,
about 1.5 h at 10 jobs.

## 1. What and why
- Rows: -4.8 V / 1 us at 500 us + k T / 6 (A206's positions; T = the settled period, N0 0.511 us, N75 / S75 0.391 us
  from A230's full-load records) - N0 and N75 at k 0 / 2 / 4, S75 at k 0; 25 C, one module, plant V7.
- Arms: d0 = the final configuration before A229 (V7, A222's trims, skipping); b = the adopted configuration (A229).
- The oracle (A142, a142_oracles.check, K4 window 1 us) classes events; K3 = a phase restarting its valley tracking,
  NEW = a spike not explained by a known class.
- Not tested: ff / ss device corners, 0 / 125 C, L x 0.7 / 1.3, four modules, -8 V / 1 us.

## 2. Criteria (arm b)
- z1: no K3 and no NEW event from the step on, every row.
- z2: run completes, whole-run peak <= 200 A, V_DS <= 40 V, no overlap or shoot-through, Vo within 1 % over the last
  20 us.
- d0 is information: it says whether the events are the plant version's or the controller's.

## 3. Predictions (not criteria)
- d0: K3 restarts on N0 at 1-2 of 3 positions (V6 had 3 at one position); N75 similar; peaks 170-180 A.
- b: as d0 within 2 A on peaks; the events unchanged (the falling step lowers Ton, the derivative term acts in the
  rising-Vo direction only briefly).

## 4. Decision rule
- z1 and z2 pass: item 3 closes on V7 with the adopted controller (named as the tested rows).
- z2 passes, z1 misses: item 3 stays open; the next step is a diagnosis of the restarts on the records (no fix run here).
- z2 misses: the adopted controller has a new problem on this row; it is traced before anything else.
