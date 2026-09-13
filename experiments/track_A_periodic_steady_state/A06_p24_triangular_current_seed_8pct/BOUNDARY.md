# A06 - P24 triangular interleaved-current seed, 8% model branch

- Compared with A05.
- Only changed input: four inductor initial-current seeds.
- At the phase-1 origin, the ideal P24 triangular waveform and T/4 shifts give
  `IL1/IL2/IL3/IL4 = 0/34.0909/68.1818/102.2727 A`.
- These are derived solver guesses. They are not voltage/current sources and
  are not accepted unless the full state closes after one period.
- The A05 full topology, 8% threshold, local-voltage readiness supervisor,
  device Coss, capacitor seeds and all other parameters remain unchanged.
- Pass requires smaller full-state residuals than A05 and actual exercise of
  the -10 A threshold. A completed run or improved voltage alone is not enough.
