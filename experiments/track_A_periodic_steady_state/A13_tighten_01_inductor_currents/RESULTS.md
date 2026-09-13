# A13 results - tighten the inductor-current state group

## Outcome

Accepted as the next isolated periodic-orbit baseline. Only the four coupled
inductor-current seeds were changed relative to the A11/A12 control model.

| State residual after one period | A11 control | A13 |
|---|---:|---:|
| VC1 | +0.609 mV | -0.089 mV |
| VC2 | -0.178 mV | -0.138 mV |
| VC3 | +2.934 mV | +0.597 mV |
| IL1 | -0.271 A | +0.005 A |
| IL2 | +0.295 A | -0.031 A |
| IL3 | +0.382 A | +0.102 A |
| IL4 | -1.340 A | -0.111 A |

The maximum absolute current residual decreases from about 1.340 A to
0.111 A. The maximum capacitor residual also decreases rather than being
traded for the current improvement. No electrical or control parameter was
changed.

This remains an isolated 1 V output-clamped periodic-state calculation. It is
not zero-start, passive-balance convergence, or output-regulation validation.
