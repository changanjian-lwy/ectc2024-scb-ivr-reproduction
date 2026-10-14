# A226 - the no-load row's reference for A224's e5 (BOUNDARY)
Method: cosim, cfg only. Track A. Written after A224's z_N0_0_d355 result, committed before A226's runs, while
A224's last stage-2 runs are still going.
Decision it changes: whether A224's e5 miss on N0 with no load comes from the derivative term (then the D term is
held while skipping, A227) or from my reference (then A224's combination can be judged against the right one).
Cheaper check done first: A224's and A221's records (below). Budget: 2 runs, about 1 h.

## 1. What and why
- A224's e5 for N0 no load asked for true valleys no more than 1 A below A221's -21.2 A. z_N0_0_d355 gives
  -23.1..-15.6 A (record A224_p24_damped_loop/cosim/run_z_N0_0_d355.json): a miss by 0.9 A.
- That reference is not the same configuration: A221 ran N0 with the V6 trim (ton_s 23.4 ns); A222 moved it to
  23.4375 ns, and A224's row has the new trim, the gate and kd. Over the last 60 us both records have 6 samples
  between pauses (303 ticks), Vo codes moving 2-3 between them (so the D term acts on 5 of them), Ton at 4.0 ns
  throughout - nothing in them shows which of the three changes moved the valleys.
- Rows: z_N0_0 on the final configuration as it is (d0: new trim, no gate, no kd) and with the gate only (g25).
  The third arm is A224's record.

## 2. Criteria / decision rule
- r1: d0's true valleys (a221_analyze.true_valleys, the same window rule) against d355's -23.1 A minimum.
  - d0's minimum within 1 A of -23.1 A (<= -22.1 A): the miss is the reference's. A224's e5 for this row is judged
    again against d0 (no more than 1 A below d0's minimum); if it passes and A224's other rows pass, the gate and
    kd 355 join the final configuration.
  - d0's minimum shallower by more than 1 A: the D term changes the no-load skipping; A227 holds d_term at 0 while
    the module skips, and the three skipping rows are run again.
- g25 is reported (the gate should be inert at constant Vin; A223's pairs were bit for bit the same through
  80 us of skipping).

## 3. Predictions (not criteria)
- d0 -22.0..-23.5 A (the trim moved the start-up and therefore the ladder at 300 us; A221 showed the ladder
  settling only by 750 us); g25 bit for bit d0.
