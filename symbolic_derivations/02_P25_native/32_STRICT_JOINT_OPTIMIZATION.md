# P25 strict joint optimization audit

## Feasibility contract

The optimizer is only a search tool.  A numerical termination flag is not a
pass.  The independent acceptance gate requires, simultaneously:

- all three P25 commutation/ZVS event chains complete;
- periodic node return within 1 mV;
- periodic current return within 10 mA;
- each phase spacing within 1 ns of 666.667 ns;
- each peak current within 0.5 A of the selected analytical target;
- module average current within 0.5 A of 66.667 A;
- negative-current fraction remains inside 5%-10%;
- when explicitly enabled, each flying-capacitor voltage return is within
  1 mV.

These tolerances were fixed before judging candidates and were not relaxed to
turn a near miss into a pass.

## A. Printed-equation branch, paper parameters frozen

Fixed: 22 nH, 500 ns, 0.5 MHz target spacing, zero-valley peak expression
`Ipk=2Io/(nP*nM)=44.444 A`, and P25 5%-10% negative-current range.

Two independent starts converge to the same local result:

- negative fraction reaches the 10% upper bound;
- phase spacings are about 596.89, 596.90 and 596.37 ns;
- peaks are 58.39, 58.31 and 57.28 A;
- module average current is 79.70 A;
- no strict feasible point is found.

This is a two-start local result, not a global infeasibility proof.

## B. One-parameter release

Only one paper parameter is released at a time; all other constraints remain.

- Releasing `L` moves it to 32.49 nH, independently agreeing with the earlier
  32.06-32.14 nH analytical calculation.  Full feasibility still fails.
- Releasing common `Ton` moves it to 554.64 ns because the optimizer tries to
  lengthen the phase spacing.  This worsens the peak/power error and still
  fails.

The opposing directions show why independent scalar tuning is insufficient.

## C. Joint release of L and common Ton, printed peak retained

The local fit finds:

- `L=32.0475 nH`;
- `Ton=545.856 ns`;
- period 1999.996 ns;
- spacings 666.6662, 666.6659 and 666.6635 ns;
- peaks 45.713, 45.698 and 45.096 A;
- module average current 64.497 A.

Timing and current return nearly close, but printed peak and module power do
not simultaneously close.  This exposes a mathematical identity conflict:
the printed `44.444 A` relation assumes a zero-current valley, while the ZVS
branch imposes a negative valley.

## D. Labelled negative-valley correction

For a triangular current with `Imin=-alpha*Ipk`, average-current balance gives

`Ipk = [2Io/(nP*nM)]/(1-alpha)`.

At alpha=5%, the corrected target is 46.7836 A and the negative target is
2.33918 A.  This is a mathematical extension, not a P25-explicit replacement.

With common Ton, the joint fit gives approximately 31.08 nH and 547.40 ns.
Period, spacing, peaks and power enter their acceptance bands, but node return
remains about 1.153 mV.  Step-size convergence from 1 ns down to 0.1 ns leaves
the residual unchanged, proving it is not integration-step error.

## E. Per-phase Ton sensitivity and explicit flying charge balance

Because two flying capacitors create two charge-balance equations, a labelled
control-sensitivity branch releases three phase-specific on-times.  This is
not claimed as the P25 controller.

After explicitly adding both flying-capacitor voltage-return equations:

- `L=31.1007 nH`;
- `Ton1/Ton2/Ton3=548.236/538.744/555.506 ns`;
- period 1999.998 ns;
- spacing errors below 0.001 ns;
- module current 66.341 A;
- flying-cap voltage returns 0.095 and 0.352 mV;
- peaks 47.053, 47.383 and 46.145 A versus 46.784 A target.

All gates pass except the peak-current gate: errors are +0.269, +0.599 and
-0.639 A, so the fixed +/-0.5 A requirement fails.  No tolerance is relaxed.

## Conclusion

No strict all-constraint feasible point has been found in the tested local
branches.  The calculation nevertheless isolates three separate issues:

1. 22 nH is inconsistent with the 500 ns/44.444 A ideal ramp; about 31-32 nH
   repeatedly emerges once timing and power are included.
2. The zero-valley peak formula and a 5% negative valley cannot both express
   the same average current without correction.
3. After that correction, flying-capacitor charge balance and equal per-phase
   peak current require additional device/control information; per-phase Ton
   freedom almost closes the system but is not documented by P25.

Required confirmation is therefore specific: the authors' definition and
measured value of phase peak current, actual per-phase gate timings, exact
flying/snubber capacitances and nonlinear Qoss, and whether the controller
applies common or phase-specific timing corrections.

## Numerical records

- `numerical_runs/02_strict_joint_fit/strict_joint_fit.json`
- `numerical_runs/03_one_parameter_release/one_parameter_release.json`
- `numerical_runs/04_L_ton_joint_release/L_ton_joint_release.json`
- `numerical_runs/05_negative_valley_corrected/negative_corrected_joint_fit.json`
- `numerical_runs/05_negative_valley_corrected/negative_corrected_refined.json`
- `numerical_runs/05_negative_valley_corrected/step_convergence.json`
- `numerical_runs/06_per_phase_ton_sensitivity/per_phase_ton_fit.json`
- `numerical_runs/06_per_phase_ton_sensitivity/per_phase_ton_charge_refined.json`
