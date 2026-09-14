# P24/P25 reported-waveform audit

## P24 ECTC 2024

The paper is analytical and conceptual rather than an experimental prototype
report. Relevant evidence labels are:

- Fig. 4: theoretical key waveforms;
- Table I: numerical calculation across phase/module/frequency choices;
- Tables II/III: literature-based magnetic/component sizing analysis;
- Figs. 5/6: conceptual package architecture and estimated dimensions.

P24 does not publish measured gate timing, measured switch-node transitions,
measured Coss, an exact added parallel capacitor, dead time, ZCD delay, or a
zero-start procedure.

## P25 APEC 2025

P25 experimentally validates a related lower-voltage implementation:

- 12 V input, 1 V output;
- nominal 0.5 MHz switching;
- 200 W total, 67 W per module;
- three phases and three interleaved modules;
- Fig. 4: high-side and low-side `Vgs`, phase handoff/delay, and corresponding
  `Vds` traces used to demonstrate ZVS;
- Fig. 5: one phase-inductor current and the summed current of Module 1;
- Fig. 5 current traces are captured at 100 kHz, not nominal 500 kHz, because
  of current-probe frequency limits.

P25 supplies implementation evidence and measurement types, but its measured
values must not be treated as direct 48 V/5 MHz P24 target values.
