# A33 compiled P25-NP4 event-ring results

LTspice completed normally. The generated controller contains one rotating
20-state machine and no absolute `T/4` release rules.

| Event | Time |
|---|---:|
| H1 off | 17.5020 ns |
| L1 on after low-side Vds zero | 17.6390 ns |
| L2 off at 9% negative target | 23.7922 ns |
| H2 on at high-side Vds zero | 26.0958 ns |
| H2 Vds at admission | -0.461 mV |

The physical event order and local H2 ZVS condition pass. The first H1-to-H2
spacing is 26.095 ns, not the nominal 50 ns, so the run does not pass the P24
5 MHz four-phase timing boundary.

Status: **CONTROLLER COMPILATION PASS / LOCAL EVENT PASS / GLOBAL TIMING FAIL**.
