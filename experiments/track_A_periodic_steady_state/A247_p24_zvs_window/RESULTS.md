# A247 - the soft turn-on window against the low-side turn-off current (D57 against the records) (RESULTS)
Boundary: 79d323a. Data: the plant-V7 records of A229-A246, 403 distinct runs of 491 files. They hold 1,267,591 learned
turn-ons of phases 2-4, of which 1,097,940 have i_off <= -5 A (a247_records.py). D57 traces: a247_window.py. Analysis:
a247_analyze.py -> a247_summary.json. Figure: a247_figure.py -> a247_zvs_window.png. Release records-a247 holds the
extracted table and the traces. Changes made after the first run are listed in Section 2.

## 0. Verdict
- **c1 fails as registered on one board: L x 1.3** (3.813 nH, A235's corner rows, 14,341 rows): median 1.10 V,
  agreement 70.1 %. It passes on the other four boards: median 0.50-0.89 V, agreement 93.3-98.0 %. By the rule, D57
  misses a block, which has to be added before step 2.
- **The block (post hoc; figure (c)):** D57 is off by a constant shift and offset.
  - The plant's swing starts about 1.5 ns after the recorded low-side turn-off, and the node sits 0.92 V higher.
  - With these two global numbers the RMSE falls from 0.99 to 0.27 V. Every board then passes c1: median 0.08-0.35 V,
    agreement 96.1-99.6 %.
  - m1's GP lowered the RMSE by 38 %, so a block is missing (>= 20 %). But it ranked dv_err and the rail first; it was
    the residual's dependence on the delay that named the block.
  - Likely sources, not yet checked: the low-side turn-off's gate delay and its 72 A/ns edge (A145), and the 50 pH loop
    with its 0.82 Ohm damping (A144). Both were added to the plant after D57.
- **c2 passes with K = 1. The soft windows nest** (figure (a)): a larger negative current gives a wider window around
  the same middle.
  - So one delay per board, phase group and rail keeps V_DS <= 2 V over +-0.5 ns on 98.4 % of the rows that have a
    window. Without the rail: 96.6 %. At a 1 V threshold: 96.6 %.
  - The delays at 12 V (D57 as registered; +1.5 ns with the correction), phases 2-3 / phase 4:
    - N0: 10.7 / 9.6 ns;
    - N75: 9.25 / 8.3 ns;
    - L x 1.3: 12.2 / 10.95 ns.
  - The size of the current is not needed, so no current comparator has to be asked about.
- **Why the learner drifts.** With a full swing the node clamps near -2.2 V (reverse conduction), so the "valley" is a
  flat bottom and the learner can follow either end of it.
  - On the rows with a window, its delays fall inside D57's window on 77.7 %, at a median 0.72 of the way to the end;
    16.0 % fall after the window and 6.3 % before it.
- **What one delay per board would change (open loop).**
  - On all 1.1 M negative-current turn-ons it gives the same V_DS as the learner: median 4.29 against 4.34 V, p99 9.16
    against 9.45 V. Most of these are valley turn-ons with no window.
  - The difference is where the learner is more than 2 ns off that delay: 4.9 % of the rows, 89 % of them shorter (the
    collapses). There the corrected model gives a median 0.45 V against the recorded 6.35 V; p90 8.5 against 10.3 V;
    hard 42 % against 79 %.
- **m2** (an MLP trained on the records alone, validation accuracy 99.8 %): its windows nest too. Their starts are
  1.8-3.5 ns later than D57's (the shift). The one end inside the records' range agrees within 0.4 ns.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| c1 | per board: median <= 1.0 V, agreement >= 90 % | **miss on L x 1.3** (1.10 V, 70.1 %); pass on N0, N0 at 125 C, N75, S75h. With the post hoc correction all five pass |
| c2 | some K <= 8 covers >= 95 % | pass, K = 1 (98.4 %) |
| m1 | GP gain >= 20 % means a missing block | gain 37.8 %, so a block is missing. Relevance: dv_err 14.6, rail 10.6, delay 6.4 (the delay named it, post hoc) |

## 2. Changes after the first run (bugs; criteria unchanged)
- The registered table had L 2.2 and 2.933 nH only, but the records also hold L x 1.3 (3.813 nH, A235). 3.813 nH was
  added; the c1 miss above is on that board.
- The board names were built wrong (cosmetic only).
- c2: a current bin with no window on D57's grid got no delay, so its rows counted as uncovered and the coverage fell
  as K grew. Such a bin now takes its valley time.
- Post hoc additions, labelled in the summary: c2 at 1 V; the shift / offset fit and c1 with it; where the learner's
  delays sit in the window; one delay per board against the learner.

## 3. Predictions
- Held: c1 on N0, N75 and S75h; m1's gain (predicted 10-30 %, got 37.8 %).
- Missed:
  - "K = 1 covers < 80 %": it covers 98.4 %. I had not seen that the windows nest.
  - The window starts: they are 1.7-4.9 ns earlier than predicted (-30 A: 4.95 against 9.8 ns); the ends are within
    1.1 ns.
  - "The learner is hard on 5-15 %": it is 58 % at 2 V, because inside the window it sits at 1.9 V, next to the line.
  - The L x 1.3 board was not in the registered list.

## 4. Limits and next
- Everything here is open loop. A fixed delay changes the currents it then sees; the closed loop is step 2 (D63's
  learner block), which must carry the correction or the edge and loop blocks.
- D57 uses Coss at 25 C, and one shift / offset serves all boards.
- A controller would need its own board's delay. It could learn it slowly from reports whose valley is well defined
  (partial swings). That is our inference; no source covers it.
- Next, by the rule: put the low-side turn-off edge and the loop into D57's free node and check that the shift and
  offset disappear. Then step 2 compares the present learner with one delay per board in D63's closed loop.
