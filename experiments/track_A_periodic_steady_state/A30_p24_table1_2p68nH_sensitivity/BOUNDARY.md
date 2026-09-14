# A30 boundary

- Parent: A28 P24 2% event-scheduler branch.
- Only changed electrical parameter: `LPHASE`, from 1.4667 nH calculated from
  the printed equation to 2.68 nH printed in P24 Table 1.
- The inherited periodic seed is not recomputed. Therefore this is a one-cycle
  direction/sufficiency sensitivity, not a periodic-state reproduction.
- No timing, Coss, clamp, threshold or timestep fitting is allowed.
