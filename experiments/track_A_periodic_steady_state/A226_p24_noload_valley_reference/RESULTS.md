# A226 - the no-load row's reference for A224's e5 (RESULTS)
Boundary: 4da5415. Records: release records-a226 (2 cosim records, logs). Runs from 4da5415,
cosim_sources_modified False. N0 released to no load at 300 us, to 750 us, plant V7, A222's N0 trim (23.4375 ns).

## 0. Verdict
- **r1: the miss is the reference's.** The final configuration as it is (d0: no gate, no kd) gives true valleys
  -22.8..-15.6 A over the last 60 us (record cosim/run_z_N0_0_d0.json), within 1 A of A224's kd 355 (-23.1 A). A221's
  -21.2 A was the old trim's. By the rule A224's e5 for this row is judged again against d0: -23.1 >= -23.8 A, pass.
- The gate alone (g25) is bit for bit d0 (sections, edge lists, peaks): inert at constant Vin while skipping.
- Vo over the last 20 us 1.0018-1.0054 V (d0 and g25).
- So the final configuration on V7 with A222's trim sits 2.8 A outside the -20..-12 A band at no load (A221
  reported 1.2 A with the old trim): the skipping line's no-load figure moves to -22.8 A.

## 1. Limits
- One row, one load; the trim's effect on the other skipping rows is A227's z_N0_10_d0.
