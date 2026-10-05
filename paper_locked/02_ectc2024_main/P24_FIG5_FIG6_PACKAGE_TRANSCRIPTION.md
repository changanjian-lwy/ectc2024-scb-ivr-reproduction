# P24 Figs. 5-6: package transcription (gate for the package layer)

Source: P24 (ECTC 2024) Sec. IV-B, Fig. 5 (a-d), Fig. 6, Table 3. Read 2026-10-05 from the PDF at 300 dpi. Only what
the figures print or show is LOCKED; everything else is MISSING and enters a model only as a labelled scenario.

## LOCKED (printed)
| item | value | where |
|---|---|---|
| architecture | 48/1 V, 1 kW, 4 phases x 8 modules (M1-M8), 1 MHz | Fig. 5 caption, text |
| package footprint | 25 mm x 40 mm | Fig. 5b |
| module footprint | 10 mm x 10 mm; modules in pairs left / right of a central strip (M1/M2 ... M7/M8) | Fig. 5b |
| central strip | one Vo and one GND bus with via arrays, along the 40 mm length, between the module columns | Fig. 5b-d |
| phase inductors | Lk = one 10 mm column per phase (4 drawn units each); L1 next to the central strip, L4 outermost | Fig. 5b-c |
| stack-up (bottom to top) | GaN dies on a heat spreader; solder resist; ABF build-up (Cu); glass substrate 1 with embedded series capacitors C1-C3; ABF build-up; glass substrate 2 with embedded inductors L1-L4 and Co (central) | Fig. 5c-d |
| switch-node vias | VP1-VP4 through glass 1, from the dies' ABF to the inductors | Fig. 5c-d |
| Vo routing | inductor outputs to an ABF layer between the glasses, laterally to the central Vo vias | Fig. 5c-d |
| input | +Vin at the centre, Cin under the central strip; DH1 next to it, QH4 outermost | Fig. 5c |
| ground | low-side sources SLk to a GND layer in the lower ABF, to the central GND vias | Fig. 5d |
| die / spreader | GaN die row 0.5 mm high (die + spreader); one die drawn 2.8 mm wide | Fig. 5c |
| devices (8 modules) | QH: 1 x EPC2067, QL: 2 x EPC2067 per phase | Table 3, text |
| placement in the processor package | IVR 40 x 25 mm at the centre of the back side of an estimated 97 x 84 mm 1 kW processor package | Fig. 6 |
| future work named by P24 | "the interconnection losses of copper and via inside the package" | Sec. IV-A, last paragraph |

## MISSING (no value in P24)
- copper thickness and layer count of the ABF build-ups; via diameter, pitch and count (switch-node, Vo, GND, Vin);
- glass thicknesses; the relative position of a module's QH and QL dies (the front section (c) cuts M1 / M2, the back
  section (d) cuts M7 / M8), hence every commutation-loop length and inductance;
- series / output / input capacitor technology, ESR and ESL; the processor-side connection of Vo / GND.

## This reproduction vs Fig. 5 (deviations, already in force)
- 4 modules x 250 W at 2.5 MHz (A124 / C05-C13; D64: 1 MHz does not pay in-package) instead of 8 x 125 W at 1 MHz;
  per phase QH 2 x / QL 3 x EPC2067 (Table 3, nM = 4). The package layer keeps Fig. 5's per-module layout (10 mm
  module, central Vo / GND / Vin strip, phase order L1 inner to L4 outer) and flags each geometric scenario.
