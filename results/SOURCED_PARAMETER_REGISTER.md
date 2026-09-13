# Sourced-parameter simulation register

This register separates reported values, values calculated from a reported
equation, values transferred from the 2025 prototype, and provisional values.

| Parameter | Value used | Status | Basis |
|---|---:|---|---|
| Input/output/power | 48 V / 1 V / 1 kW | Reported | ECTC 2024 target architecture |
| Phases/modules | 4 / 4 | Reported | ECTC 2024 Table 1 case |
| Switching frequency | 5 MHz | Reported case | ECTC 2024 Table 1 |
| Inductor | 2.68 nH | Reported | ECTC 2024 Table 1; differs from printed Eq. (4) |
| GaN device | EPC2067 | Reported | ECTC 2024 Table 3 |
| Devices per switch position | HS 2, LS 3 | Reported | ECTC 2024 Table 3, four-module row |
| Equivalent typical Ron | HS 0.65 mOhm, LS 0.433 mOhm | Calculated | EPC2067 typical 1.3 mOhm divided by parallel count |
| Equivalent energy Coss | HS 3.194 nF, LS 4.791 nF | Calculated approximation | EPC2067 Coss(ER)=1597 pF times parallel count |
| Gate level | 5 V | Datasheet value | EPC2067 recommended/characterization condition |
| Flying capacitance | 27.34 uF | Calculated design input | APEC 2025 Eq. (23), allowing 0.12 V ripple |
| Flying-cap ripple allowance | 0.12 V | Provisional requirement | 1% of the ideal 12 V ladder step |
| Flying-cap ESR/ESL | 0.5 mOhm / 30 pH | Provisional | Must be replaced by the selected capacitor bank/package extraction |
| Output capacitance | 470 uF | Provisional | Placeholder bank; the papers do not give its value |
| Output-cap ESR/ESL | 0.2 mOhm / 30 pH | Provisional | Must be replaced by the selected bank/package extraction |
| Dead time | 2 ns | Provisional sweep input | Neither paper reports the 5 MHz target value |
| Input impedance | 5 mOhm + 10 nH | Provisional | Package/source impedance not reported |
| Startup | 40 us rail ramp, PWM enabled at 5 us | Provisional test condition | No startup controller is reported |

The 2025 prototype identifies GS61008T, 1EDBx275F, Coilcraft 1212VS-22N,
and partial Murata family strings GRM32EC72 and GRM219R60. Those values are
not copied directly into the 48 V target because the prototype is 12 V,
200 W and 0.5 MHz. The incomplete capacitor strings do not uniquely identify
capacitance, voltage rating, ESR or ESL.

The netlist deliberately contains no capacitor-voltage initial conditions.
Failure to establish the 36/24/12 V ladder therefore indicates a missing
startup/control mechanism rather than being hidden by initialization.

## First transient run (no precharge)

LTspice completed a 500 us startup transient.  The input ramps from 0 V to
48 V in 40 us and fixed open-loop interleaved PWM is enabled after 5 us.

| Quantity | Result |
|---|---:|
| Calculated flying capacitance | 27.34375 uF |
| Output voltage, average over 480-500 us | 0.35414 V |
| Module 1 C1 voltage, average | 12.9705 V |
| Module 1 C2 voltage, average | 8.6258 V |
| Module 1 C3 voltage, average | 4.3470 V |
| Module 1 L1 maximum current | 22.768 A |
| Module 1 L1 minimum current | -3.245 A |
| Peak source current during startup | 200.927 A |

This run does **not** reproduce the nominal 1 V output or the expected
36/24/12 V capacitor ladder.  It establishes a useful negative result:
the reported steady-state topology plus fixed PWM does not, under the stated
provisional parasitics and startup ramp, autonomously establish the intended
operating point within 500 us.  A startup/precharge sequence, active capacitor
balancing, current limiting, or a validated controller law is still required.

The result must not yet be used as an efficiency prediction.  The switch model
uses datasheet-derived equivalent Ron and Coss rather than the manufacturer's
nonlinear transistor model, and the capacitor parasitics and dead time remain
provisional.
