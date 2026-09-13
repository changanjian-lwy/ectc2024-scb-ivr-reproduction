# Step 07 - R03 precharge-to-PWM takeover

## New modulation-source lock

Roberts and Prodić, IEEE OJPEL 2024, DOI
`10.1109/OJPEL.2024.3417017`, establishes the following constraints relevant to
the P24 four-phase module:

- adjacent main-switch ON intervals must not overlap if nominal reduced switch
  stress is to be retained;
- for `N=4`, rearranging phase order cannot extend equal per-phase duty beyond
  `1/N=25%` without increased stress;
- the P24 value `D=1/12` is below this limit, so conventional sequence
  `1 -> 2 -> 3 -> 4` is a valid steady-state modulation baseline;
- star sequences introduced by that paper apply to `N>=5`, not this module;
- its large-signal appendix assumes forced CCM/CVM and state durations that do
  not depend on reactive states, so it does not define P24/P25 boundary-mode
  startup takeover.

## Legacy lessons applied

- R00: no direct zero-state PWM startup.
- R01A-D: no instantaneous comparator/latch network before startup physics is
  established; event chatter is not a power-stage verdict.
- I0T: bypass-generated state is not a literature-supported precharge.
- I0U/I0V: do not change damping and control together; a raw zero-cross switch
  is not yet a validated controller.
- R02B: `CDIV=1.076 mF`, `TRAMP=100 us` is only a sensitivity point with a
  physically generated imperfect ladder, not a P24 parameter.

## R03A isolated purpose and boundaries

R03A connects the R02B passive network to the actual one-module P24 Fig. 3
power stage. At `150 us`, it applies 20 periods of fixed 5-MHz, `D=1/12`,
conventional four-phase PWM.

The only purpose is to test whether takeover causes immediate capacitor-ladder
collapse, shoot-through-scale input current, or unbounded phase current.
Complementary low-side timing is a diagnostic baseline, not a claim of the
P24/P25 CCM-DCM boundary controller. No zero-crossing, negative-current target,
Coss, dead time, device model, or closed-loop output controller is added.

## R03A result

Status: **FAILED_FIXED_PWM_TAKEOVER / NUMERICALLY_COMPLETED**.

The ladder was generated from zero and measured immediately before takeover as
`34.0456/21.7934/10.6309 V`. After 20 switching periods it was
`34.6071/22.3057/10.9179 V`; therefore it did not immediately collapse.

However:

- `Vout` reached `1.53694 V` (peak `1.53732 V`);
- phase-current maxima were `884.36/745.07/625.63/563.46 A`;
- the post-takeover input-current peak was `42.44 A`.

The diagnostic therefore fails on output overshoot and accumulated inductor
current, not on immediate precharge-ladder collapse or source shoot-through.

### Causal interpretation

At startup `Vout` is low, so the OFF-interval inductor slope `-Vout/L` is too
small for current to return to zero before the next fixed 5-MHz opportunity.
Applying the steady-state Table-I period immediately therefore drives the
converter into current accumulation. This independently confirms the earlier
R00/R01 lesson without using preset capacitor voltages.

### Boundary created by this failure

No further fixed-complementary takeover run is justified. R03B must introduce
only a state-dependent DCM/PFM release law: variable effective off-time or pulse
skipping until zero-current detection, followed later by the P25 slight-negative
current interval for ZVS. Device-level ZCD thresholds/delay must remain symbolic
until supplied; the P24 `125 A` phase peak may cap normal phase current but is
not a startup-source-current limit.

The ISSCC-2019 FIVR source cited by both P24/P25 supports the control family:
output-comparator pulse triggering, variable ON-time for peak-current control,
ZCD across the low-side device, and programmable forced off-time (about 1 ns in
its own low-voltage IC). Its numeric comparator/delay values are not transferable
to this 48-V GaN SCB without author data.
