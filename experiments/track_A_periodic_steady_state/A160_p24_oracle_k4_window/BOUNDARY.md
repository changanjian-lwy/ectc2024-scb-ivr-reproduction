# A160 - the oracle's K4 window under slow turn-ons (BOUNDARY)
Method: analysis only (A142's oracles on existing records; no new runs)
Track A, verification tooling. Written and committed before the scan; a142_oracles gains K4_US (default 1.0, unchanged
behaviour) in the same commit.
Decision it changes: whether A142's K4 class ("spike within a line ramp + 1 us or a load step + 1 us") widens to + 2 us,
so that the post-step period swing under a slow turn-on stops raising NEW flags.
Cheaper check done first: the ten known cases (A154 f200_off48 / f300_off24, A158 q15_s100 / q30_s100, A159 s150 l_p48_1us,
L13_l_p48_1us and four modules x 4): each is phase 1's second post-step swing peak, 168-176 A, at ramp + 1.01-1.49 us.
Budget: one scan of the local records of A142-A159, C13, C14 and the ML folder's A14x-A15x (~600 files, ~10 min).

## 1. Criteria
1. All ten known swing-peak events are K4 at 2.0 us.
2. Every other event the wider window reclassifies is a "spike" whose current is not above its run's post-step peak.
3. No run with a NEW event that a RESULTS traced to a real mechanism loses its flag: A142 z104, A150's oscillating rows,
   A157 / A158's Q >= 100 and undamped rows, A151 on9_l100_l_p48_1us.

## 2. Decision rule
- 1-3 pass: K4_US becomes 2.0 (D63 / scb-map / RESULTS of A154 / A158 / A159 note the change; their stored summaries
  are not re-analysed).
- 2 or 3 fails: K4 stays at 1.0 and the slow-turn-on swing peaks stay documented exceptions.
