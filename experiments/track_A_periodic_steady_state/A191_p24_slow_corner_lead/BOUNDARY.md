# A191 - a 9.5 ns high-side lead against the slow corner's post-step valley loss (BOUNDARY)
Method: mixed (cosim, plant V5, code cfe581f; cfg only: driver hs_on_lead_ns 8 -> 9.5, still ramped over 20 us)
Track A, package layer. Written and committed before the runs.
Decision it changes: whether slow devices with L x 0.75 / 0.8 hold 200 A at 125 C after +4.8 V / 1 us with a longer
lead for slow boards, read from the 25 C trim like A190's table. That would close A187 without an RTL change.
Cheaper check done first: A163 / A164 / A169 / A171 records.
- A163: a predictive turn-on is late once the gate delay exceeds ~5.5 ns on phase 4 beyond the lead, and the slow
  corner's turn-on delay is 9-20 ns.
- The lead was held at 8 ns because a lead longer than the delay shot through (A164 / A169). Since A171 the
  threshold interlock holds such a gate until the complement stops.
- The bridge bounds the lead below t_drv (10 ns, the driver's own delay), so 9.5 ns is the largest step available.
Budget: 12 runs (A187's, lead changed), --jobs 6, ~3 h.

## 1. What and why
- A187: in every run phases 3-4 lose their valley for ~25 us after the step (28-65 late fires), Vo dips and Ton rises
  ~20 %. At 2 of 6 step positions per board, a recovering valley meets that Ton and the peak exceeds 200 A
  (204.5 / 207.2 A at L x 0.75, 217.1 / 201.5 A at L x 0.8). A longer lead attacks the late fires themselves.
- Runs: A187's 12 cfgs with the lead at 9.5 ns. The step lands at a phase read after the fact; it may differ from
  A187's. A187 is the reference run for run.
- Not tested: other corners with 9.5 ns (shoot-through is prevented by the interlock, but nominal / ff timing is not
  checked here); other rows; 25 C.

## 2. Criteria (per run, A187's)
 c1 start-up / handover <= 200 A;  c2 post-step <= 200 A;  c3 V_DS <= 40 V, COMPLETED, 0 shoot-throughs / overlaps;
 c7 Vo <= 1.05 V over 0-300 us. A board holds if c1-c3 pass at all six positions.
Diagnostic: late fires on phases 3-4 in the first 30 us after the step, and the post-step Vo minimum, against A187.

## 3. Predictions (not criteria)
- Late fires on phases 3-4 fall by >= 50 % against A187; Vo minima >= 0.988 V; post-step <= 200 A at every position
  on both boards. Least certain: whether 1.5 ns is enough (the slow corner's delay spread is wide).

## 4. Decision rule
- Both boards hold: a per-corner lead (9.5 ns for slow boards, read from the 25 C trim) is the candidate. Before it is
  adopted, a follow-up checks the nominal and ff corners with it, since it would apply only to slow boards.
- Late fires fall but peaks still exceed 200 A: the lead helps but is not enough within t_drv. The slow corner's
  limit stays open (controller / driver path).
- Late fires do not fall: the lead is not the lever; named.
