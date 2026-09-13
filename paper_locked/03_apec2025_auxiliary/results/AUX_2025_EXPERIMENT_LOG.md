# AUX-2025 supporting experiment log

## AUX-2025.0 - Earlier-model audit

See `PF_A1_OLD_MODEL_AUDIT.md`. The earlier fixed-timing model transferred
power and maintained the initialized 8/4 V ladder, but had 59.79 A peak
current and 5.22 V high-side VDS before turn-on. It did not reproduce ZVS.
The calibrated replay changed the paper operating point to 0.623 MHz and
`D=0.298`; it is not the new baseline.

## AUX-2025.1 - Equation-timed high side, published 5% boundary target

**Paper boundary held fixed**

- 2025 Fig. 1 one three-phase module, 12 V to 1 V, 67 W.
- 0.5 MHz (`T=2 us`), phase shift `T/3`, 22 nH, 0.5 mOhm winding
  resistance.
- Equation-(17) duty `D=nP*Vo/Vin=0.25`, hence `Ton=500 ns`.
- Paper measured current target about 50 A peak.
- Section-III negative-current design case: 5% of 50 A = -2.5 A.

**Unresolved variables exposed rather than claimed as paper values**

- `CFLY_TEST=120 uF`, `COUT_TEST=470 uF` and their ESR values are retained
  only as sensitivity-baseline values because Table III omits full suffixes.
- No added snubber is used in this first run (`CSNUB=0`). The GS61008T
  datasheet typical Coss is represented as 250 pF per high-side device and
  500 pF for two parallel low-side devices.
- The GaN reverse-conduction clamp remains a simplified numerical model, not
  a manufacturer SPICE model.

**Only control change relative to the old fixed-timing run**

The low-side switch is no longer opened at an arbitrary 300 ns-before-period
time. It is held through the zero crossing and opens at the paper-derived
`-2.5 A` target. The high-side clock, frequency and on-time are not tuned.

**Result, 90-100 us**

| Quantity | Result | Acceptance |
|---|---:|---|
| Vout average | 1.02286 V | close, not a pass criterion alone |
| IL1 maximum | 59.11 A | FAIL vs. measured about 50 A |
| IL1 minimum | -2.513 A | PASS for the selected -2.5 A boundary target |
| IL1/IL2/IL3 average | 23.02/22.44/23.06 A | approximate sharing |
| Load average | 68.53 A | close to 67 A/module |
| VCs1/VCs2 average | 8.079/3.999 V | expected ladder retained |
| VCs1/VCs2 ripple | 0.243/0.242 Vpp | sensitivity value only |
| High-side VDS before next turn-on | 3.960 V | FAIL: no ZVS |

**Conclusion**

The paper-derived negative-current boundary can be imposed without changing
the 0.5 MHz/500 ns operating point, but that alone does not align Mode 5
commutation with the next Mode 6 high-side turn-on. The run must not be called
a reproduction success. The next experiment must diagnose the Mode 2/5
commutation timing and the missing `CH/CL` values; it must not alter frequency,
duty, inductance or the -5% target merely to improve the displayed numbers.

## AUX-2025.2 - Snubber-capacitance sensitivity at the same boundary

**Compared with:** AUX-2025.1.

**Only changed variable:** an equal added capacitance on each published `CH`
and `CL` position: 0, 250 pF, 500 pF, 1 nF and 2 nF. All paper operating
conditions, `Ton=500 ns`, `L=22 nH` and the -2.5 A target remain frozen.

| Added CH/CL | Vout (V) | IL1 peak (A) | IL1 valley (A) | VDS before high turn-on (V) |
|---:|---:|---:|---:|---:|
| 0 | 1.0229 | 59.11 | -2.513 | 3.960 |
| 250 pF | 1.0279 | 58.55 | -2.518 | 3.900 |
| 500 pF | 1.0093 | 58.61 | -2.523 | 3.969 |
| 1 nF | 1.0242 | 59.05 | -2.541 | 3.959 |
| 2 nF | 1.0437 | 59.30 | -2.570 | 3.919 |

**Conclusion:** changing the unpublished snubber value across this broad
range does not make the fixed 2 us clock land on the ZVS instant. In every
case VDS briefly reaches the reverse-conduction clamp, but has returned to
about 3.9 V by the scheduled high-side edge. Therefore the next experiment
must implement the paper's event sequence: the negative-current low-side
turn-off initiates Mode 5, and the high side must be enabled at the ensuing
VDS zero event. Treating 0.5 MHz as an immutable edge schedule conflicts with
the paper's adjustable-on/off-time boundary controller; it is a nominal
operating frequency, not permission to ignore the commutation event.
