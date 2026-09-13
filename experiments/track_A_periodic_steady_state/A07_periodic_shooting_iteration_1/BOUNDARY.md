# A07 - periodic shooting iteration 1

- Compared with A06.
- Only changed input: initial four-inductor current vector.
- New vector equals A06's measured final vector after exactly one 200 ns
  period: `[-0.446817, 3.595266, 40.663224, 85.442069] A`.
- This is a fixed-point solver step for `state(T)-state(0)=0`, not parameter
  fitting and not a forced waveform.
- Topology, capacitor states, device Coss, 8% branch, voltage supervisor,
  switching frequency and timing remain unchanged.
