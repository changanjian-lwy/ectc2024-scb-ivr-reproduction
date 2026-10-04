# C08 - the four-module final design with A136's phase-1 cap (RESULTS)
Boundary: afb277b. Records: cosim/run_*.json (20); c08_summary.json.

## 0. Verdict
- **The L+ cap lock exists on four modules and A136's cap removes it:** every module at L x 1.2, +250 A at 1000 us -
  with A128's absolute cap all four modules lock (ladder deviation 10.5 %, Vo 0.917 V, 216 A); with A136's cap none
  does (1.12 %, Vo 1.000 V, 177.8 A).
- On C06's 18 rows the hard constraints hold (no overlap, peak after the start-up <= 183.4 A, locked, post-step
  peaks <= 183.4 A) and the post-step peaks track C06 within 2.4 A on 9 of 10 stepped rows.
- **Not adopted yet** (criterion 1's "no new failure" and criterion 2 fail):
  - late fires: every row's totals rise (n0 [5, 3, 1, 4] vs C06's 0-2; m3n 118-137 per module vs 8-26). Stepped rows
    carry n0's counts unchanged, and the master's record (from 243 us) has no off-slot period: they come from the
    handover, A136's start-up regression (A137).
  - m3n's turn-off current sd 0.11-0.12 A in the end window (C06 0.01 A, limit 0.06 A): a steady-state difference
    the start-up does not explain by itself; not traced.
  - s_m25: post-step peak 153.4 vs 146.1 A (+7.3 A, limit 7 A) and step_10pct; inside A129's 2-7 A step-timing floor
    plus 0.3 A, not traced.
- Next: rerun the 18 rows with A137's restart (C09) if A137 is adopted, and trace m3n's end-window sd there.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | hard constraints / no new failure | hard: pass on 18 rows; **no new failure: fail** - late_fires on 15 rows (start-up), sd_band on m3n, step_10pct and c06_within_7a on s_m25 |
| 2 | post-step peaks within 7 A of C06 | **fail** on s_m25 (+7.3 A); others -1.5 to +2.4 A |
| 3 | l12a locks, l12q holds | pass (above) |
Predictions: 18 rows within a few A of C06 - yes on the hard numbers, not on the late-fire counts; l12a locks /
l12q holds - right.

## 2. Limits
- The late-fire origin rests on equal counts across rows and a clean recorded window, not on a handover trace.
- Start-up peaks 190.6-198.8 A (C06: <= 185 A), all from the handover; judged only after 600 us, as registered.
