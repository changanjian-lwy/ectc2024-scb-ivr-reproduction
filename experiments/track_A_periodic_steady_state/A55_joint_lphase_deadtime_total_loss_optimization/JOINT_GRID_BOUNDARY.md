# A55 local L/dead-time grid: pre-run contract

Classification: sensitivity extension of A51/A55, not a native P24/P25
controller or rated-power reproduction. One module, four phases, 48 V,
fixed 5 MHz command windows, output capacitor plus fixed 4 mOhm load.

Inductance rows: previous refined passing endpoint (0.6215240418 nH), old
critical endpoint (0.6274059728 nH), and P24-equation reference (1.4666667 nH).
Dead-time columns: 1.075, 2.15 and 4.3 ns, respectively half, unchanged and
twice the inherited reference. These are local sensitivity probes within the
declared [0.5,10] ns exploration range, not hardware limits or paper values.
Each row uses its own saved periodic checkpoint as seed for every column.
No capacitor state is clamped to the seed. Three inactive divider coordinates
remain pinned under the inherited fast-subsystem contract.

EPC2067 resistance and capacitance, parallel counts, source impedance, flying
and output capacitance and fixed PWM duty remain as in A55. Complete effective
boundary fields are serialized for every probe. No load retuning, on-time
retuning or negative-current threshold control is introduced.

Solve at 62.5 ps/5 ps with inherited relative closure tolerance 1e-6. Stop an
individual probe on the inherited +/-250 A current screen or numerical failure;
record the error and continue other independent probes. Failed points cannot
rank. Re-meter converged states at their OWN dead time, reporting all high- and
low-side ZVS events, phase extrema, current at high-side dead-time entry,
negative valley and entry ratios separately, mean output voltage, mean(V^2/R)
load power, and actual enabled-channel sum integral(Vbranch^2/Rbranch)/T.

The low-side turn-off entry ratio is observational, not a commanded 1–2%/5–10%
threshold. Natural-ZVS admission still uses the ideal-clamp/channel surrogate;
reverse-conduction hardware loss remains absent. Current limit is a project
screen, not device SOA. Do not rank absolute loss across unequal delivered
power as an efficiency improvement. No power tolerance is invented to label
a point a paper match; expose continuous target errors instead.

This coarse local grid cannot establish a global optimum. A promising point
requires finer-step re-solve before numerical acceptance, followed by an
explicit rated-power/control-boundary decision before any optimization claim.

Dead-time changes also move the inherited symmetric PWM-window edges and can
change actual channel-active duration despite fixed nominal PWM duty. This is
the inherited scheduler's behavior, not an isolated capacitance-discharge-time
experiment. Record modeled high/low channel-active durations in the selected
refinement; early conduction includes the ideal-clamp surrogate, so these
durations are not measured real gate-drive pulses.
