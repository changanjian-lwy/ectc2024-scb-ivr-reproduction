# Ideal hierarchy reproduction log

## Classification and correction status

| Category | Experiments | Purpose | Status |
|---|---|---|---|
| A. Topology/timing | I0A-I0D, I0G | self-balance, phase/module shift, L comparison | valid with declared 1 mOhm regularization |
| B. Conservation/numerics | I0E-I0H, I0K-I0L | settling, hidden defaults, lossless limit, damping | active diagnostic |
| C. Ideal control | I0M-I0O | ideal voltage feedback before device parasitics | voltage target reproduced; boundary tradeoff remains |

**Correction:** LTspice assigns approximately 1 mOhm default series
resistance to an inductor when `Rser` is omitted. The earlier I0A-I0J runs
therefore contained hidden damping even though they were described as ideal.
They were regenerated with `RLDAMP=1m` explicitly declared. Their topology,
interleaving and inductance-comparison conclusions remain useful, but the
approximately 0.94 V output was caused by this resistance and is no longer
treated as an unexplained topology error.

## Scope and non-assumptions

This stage isolates the paper topology and timing before adding device and
package details. It uses ideal capacitors, an ideal 48 V source, near-ideal
switches/diodes, 5 MHz switching, and a 470 uF ideal output capacitor. Except
for the pure-lossless I0K test, inductors use an explicitly declared 1 mOhm
numerical/startup damping resistance. All flying capacitors start at 0 V.
There is no precharge circuit,
active balancing, feedback controller, ESR/ESL, Coss, dead time, input
impedance, or fixed 36/24/12 V source.

The 27.34375 uF flying capacitance is retained only as the explicit value
calculated previously from APEC 2025 Eq. (23) using a declared 0.12 V ripple
target. It is not claimed as the unpublished ECTC 2024 component value.

The one-module cases use a 250 W load; the four-module cases use the 1 kW
load. Thus the intended power per module remains 250 W in both hierarchy
levels.

## Source check

ECTC 2024 Table I explicitly gives the four-phase/four-module values at
5 MHz as Ton = 16.7 ns, Lcrit = 2.68 nH, and IL,pk = 125 A. The 25 MHz value
in the text is the maximum frequency allowed for a four-phase 48/1 V design
under the paper's assumed 3.4 ns minimum on-time; it is not the operating
frequency of the selected 5 MHz Table-I column.

Direct substitution into printed Eq. (4), however, gives 1.467 nH rather
than 2.68 nH. Both values are therefore tested separately rather than forced
to agree.

## I0A - Ideal one-module hierarchy check

**Compared with:** no earlier ideal hierarchy case.

**Variables:** one four-phase module, 250 W load, L = 2.68 nH.

**Result:** the zero-initialized flying capacitors naturally converged to
35.97/23.98/11.99 V. Vout = 0.9407 V. L1 = 17.0 to 94.4 A.

**Conclusion:** the capacitor ladder is a natural charge-balance result in
the ideal model; it was not imposed. The Table-I inductance does not put this
fixed-open-loop model at the CCM-DCM boundary.

## I0B - Ideal four-module hierarchy check

**Compared with:** I0A.

**Only independent changes:** four interleaved modules and 1 kW load.

**Result:** Vout = 0.9407 V; C1/C2/C3 = 35.98/23.95/11.98 V; L1 = 20.5 to
96.5 A. Peaks of L1-L4 in one module are separated by approximately 50 ns,
equal to T/4. Peaks of L1 in modules 1-4 are separated by approximately
12.5 ns, equal to T/16.

**Conclusion:** the implemented phase and module interleaving is correct.
The Table-I inductance remains in CCM rather than at the claimed boundary.

## I0C - Printed Eq. (4) inductance

**Compared with:** I0B.

**Only independent change:** L = 1.467 nH from direct substitution into
ECTC 2024 Eq. (4).

**Result:** Vout = 0.9421 V; C1/C2/C3 = 36.00/24.00/11.96 V; L1 reaches
approximately 130 A and crosses slightly below zero. Exact extrema show
some cycle-to-cycle and numerical sensitivity near the switching boundary.

**Conclusion:** the printed equation is qualitatively much closer to the
claimed 125 A boundary waveform than Table I's 2.68 nH, but the unresolved
numerical mismatch must not be hidden by selecting a preferred value.

## I0D - Ideal inductance sweep

**Compared with:** I0A.

**Only independent variable:** L = 1.40, 1.467, 1.55, 1.65, 2.00, 2.68 nH.

| L (nH) | IL1 max (A) | IL1 min (A) |
|---:|---:|---:|
| 1.40 | 131.50 | -9.12 |
| 1.467 | 128.99 | -5.81 |
| 1.55 | 123.92 | -2.34 |
| 1.65 | 120.17 | 1.42 |
| 2.00 | 107.55 | 9.80 |
| 2.68 | 94.41 | 17.02 |

**Conclusion:** under the present ideal fixed-frequency timing, the
zero-current boundary lies between 1.55 and 1.65 nH. Around 1.55 nH, the
negative current is about 1.9% of the 124 A peak, close to the ECTC 2024
description. This is a simulation diagnostic, not a replacement for the
paper's value.

## I0E/I0F - Long-settling checks

**Compared with:** I0B/I0C.

**Only independent change:** simulation duration 50 us to 500 us.

**Result:** the capacitor ladder remains near 36/24/12 V, but Vout remains
near 0.941-0.942 V. Therefore the 0.94 V result is not simply an unfinished
50 us startup transient.

## I0G - Full 16-phase near-boundary cross-check

**Compared with:** I0B.

**Only independent change:** L = 1.55 nH.

**Result:** Vout = 0.9419 V; C1/C2/C3 = 35.97/23.97/11.97 V; IL1,max =
124.61 A; IL1,min = -2.05 A. The latter is 1.65% of peak current.

**Conclusion:** the complete four-module model reproduces the paper's
claimed peak-current and small-negative-current shape around 1.55 nH, but
does not simultaneously reproduce 1 V with the theoretical 8.333% duty.

## I0H - Near-zero Ron check

**Compared with:** I0G.

**Only independent change:** ideal switch/diode Ron from 1 uohm to 1 nohm.

**Result:** Vout changes only from 0.9419 V to 0.9425 V.

**Conclusion:** the remaining output-voltage offset is not explained by
ordinary on-resistance. No efficiency claim is made from this ideal model.

## I0I/I0J - Ideal on-time and inductance diagnostics

**Compared with:** I0D.

**Independent variables:** duty ratio and inductance only. These sweeps do
not redefine the paper value; they identify what control change would be
needed in the present model.

At L = 1.55 nH, duty values 8.333/8.5/8.7/8.9/9.1/9.3% produce Vout values
0.943/0.960/0.982/1.007/1.030/1.051 V. A fine scan finds Vout = 1.0008 V
at D = 8.85%, L = 1.60 nH, and Vout = 0.99994 V at D = 8.85%, L = 1.62 nH.

**Conclusion:** fixed open-loop timing requires about 8.85% duty to reach
1 V, versus the paper's theoretical 8.333%. Because the 2025 paper explicitly
uses zero-crossing detection and adjustable on/off timing, the next ideal
layer should add an idealized boundary-mode controller before any physical
parasitics are introduced. The duty discrepancy remains a finding, not a
parameter to silently tune away.

## Current ideal-layer conclusion

1. Natural 36/24/12 V charge balance is reproduced without voltage clamps.
2. T/4 phase and T/16 module interleaving are reproduced.
3. Table I's peak and boundary current are not reproduced with 2.68 nH.
4. Approximately 1.55 nH reproduces 125 A and a 1-2% negative valley in the
   full model, while printed Eq. (4) gives 1.467 nH.
5. The theoretical duty produces about 0.942 V in fixed open loop; an ideal
   zero-crossing/voltage controller is the next model layer.

The five statements above describe the explicitly damped open-loop stage and
are superseded where applicable by the correction and controlled tests below.

## I0K - Pure lossless zero-start limit

**Compared with:** I0G.

**Only independent change:** inductor `Rser` explicitly changed from 1 mOhm
to 0. All capacitor initial voltages remain zero.

**Result:** Vout approaches 1 V, but internal currents grow to several kA
and the flying-capacitor ladder does not converge.

**Conclusion:** a perfectly lossless switched LC network started from zero
contains undamped internal modes. Matching only Vout in this run would be a
false reproduction. This case is retained as a failed stability test.

## I0L - Explicit damping sweep

**Compared with:** I0K/I0G.

**Only independent variable:** inductor regularization resistance = 0.1,
0.2, 0.5 and 1 mOhm.

At 0.1 and 0.2 mOhm the 50 us run retains large internal oscillations. At
0.5 mOhm it is close to a bounded boundary waveform. At 1 mOhm it settles
cleanly but produces the expected approximately 60 mV drop at approximately
60 A per phase.

**Conclusion:** damping is required for a zero-start transient to converge,
but it is a declared numerical/startup regularization variable, not an
asserted paper component value.

## I0M/I0N - Ideal voltage-control layer

**Compared with:** I0G.

**Only independent change:** add an ideal PI voltage controller that adjusts
high-side on-time. The 1 mOhm declared regularization remains; no device or
package parasitic is added.

After 500 us, D = 8.8427%, Vout = 1.00002 V, load current = 1000.02 A, and
C1/C2/C3 = 35.978/23.991/11.987 V. The four phase-average currents in Module
1 are 62.85/62.74/62.89/62.75 A. IL1,max = 133.12 A and IL1,min = -2.46 A.

**Conclusion:** the complete 16-phase topology can simultaneously regulate
1 V/1 kA, naturally maintain the capacitor ladder and share average current.
The required duty is higher than the paper's lossless 8.333% because the
declared 1 mOhm damping must be compensated.

## I0O - Peak-current cross-check under ideal voltage control

**Compared with:** I0N.

**Only independent change:** L = 1.65 nH instead of 1.55 nH.

**Result:** Vout = 0.99987 V, IL1,max = 126.02 A, but IL1,min = +1.69 A.

**Conclusion:** increasing L recovers the paper's approximately 125 A peak,
but loses the negative current required for ZVS. At fixed 5 MHz, the model
cannot simultaneously match 1 V, 125 A peak and a 1-2% negative valley with
one L value. The next ideal-control sublayer must explicitly control the zero
crossing/off-time rather than using complementary fixed-period PWM.

## Revised ideal-layer conclusion

1. Category A passes: topology self-balancing and interleaving are verified.
2. Category B identifies the hidden 1 mOhm inductor default and proves that
   the pure lossless zero-start transient is not a valid steady-state solver.
3. Category C reproduces 1 V, 1 kA, capacitor balance and average current
   sharing with ideal voltage feedback.
4. Peak-current and negative-valley targets cannot both be matched using only
   fixed-frequency duty and L. Ideal zero-crossing/off-time control is still
   required before adding Coss, ESR/ESL, dead time or package parasitics.

## I0P-I0S - Zero-crossing controller implementation diagnostics

**Compared with:** I0N; first reduced to one module where noted.

Analog latch, hysteretic-switch and Schmitt-trigger realizations were tested.
The latch version exposed an overlap/reset error which was corrected, but the
corrected latch and both direct hysteretic forms either produced threshold
chatter or failed to initialize in the floating multilevel network. These are
controller/numerical failures, not evidence against the SCB topology. Their
netlists and logs are retained; incomplete large RAW files were discarded.

## I0U/I0V - Zero-cross takeover after balanced startup

**Compared with:** I0T.

I0U hands control to a per-phase current hysteresis element after the ladder
has settled; I0V adds 100 ps controller propagation delay. Both generated
excessive threshold events after takeover. I0U also changed damping and
control simultaneously, so it is explicitly rejected as a controlled
comparison. I0V proves that a small delay alone does not break the power-stage
algebraic discontinuity. Incomplete RAW files were discarded.

## I0W - Variable low-side turn-off scan

**Compared with:** I0N.

**Only independent change:** retain 1 mOhm numerical damping and open each
low-side switch at an adjustable normalized cycle position `ZEND`.

The successful I0N waveform places falling zero crossings at approximately
98.4%-99.4% of the local cycle. Tests at 96% and 99% generated excessive time
steps because at least some phases were opened with nonzero inductor current.
This rejects one common turn-off fraction for all phases; it does not reject
variable off-time control. The next controller must sample/hold a separate
turn-off instant for every phase and cycle, so the decision cannot change
instantaneously in response to the current it is interrupting.
