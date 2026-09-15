# 2024 ECTC SCB-IVR Reproduction - Progress Report

## 1. Objective and overall approach

The current work is focused on reproducing the 48 V-1 V, 1 kW, four-module
four-phase SCB-IVR from the 2024 ECTC paper. At this stage the goal is not to
first make the complete system output a "correct-looking" 1 V waveform, but
to check whether the paper's stated specifications, equations, topology and
commutation sequence can form a self-consistent four-phase periodic
trajectory.

The reproduction follows three principles:

1. Content explicitly given by the 2024 paper is the primary basis; missing
   details are supplemented only from the 2025 paper.
2. Where the two papers differ, both the P24 and the P25-to-P24 branches are
   kept separate; the conditions are never merged.
3. Failure is accepted and the earliest failure boundary is recorded; results
   are never made to look good by arbitrarily changing device parameters or
   initial states.

Mihai confirmed directly (2026-09-15) that the 2024 paper's 48 V/1 V/1 kW,
four-phase/four-module configuration was never physically built or measured
by the authors; it exists only as an analytical/optimization design. The
2025 paper's 12 V/200 W, three-phase prototype remains the only real,
measured hardware in this author line. The work below is therefore
reproduction and consistency-testing of an analytical design, not an
attempt to replicate a hardware unit that does not exist, and no device or
capacitance number for the 48 V case should be read as a "measured value."

## 2. Macro-level decomposition of the framework

The reproduction is split along two directions.

The horizontal direction is the physical handoff process from one phase to
the next:

1. High side conducts, inductor current rises;
2. High side turns off, the device's output capacitance begins commutating;
3. Low side conducts, inductor current falls to zero;
4. The small negative current the paper requires is established;
5. Low side turns off, the negative current drives commutation at the next
   high-side node;
6. The next phase turns on and latches once its high-side switch reaches
   zero voltage.

The vertical direction adds model depth layer by layer at each stage: paper
specifications and equations, topology, device model, physical-event
detection, control state machine, four-phase coupling, periodic closure, and
only then zero-state startup and hardware non-idealities.

The purpose of this decomposition is that, when a result fails, the project
can answer clearly whether the problem comes from device parameters,
detection conditions, control logic, or the multi-phase energy state -- not
just arrive at an undifferentiated "the simulation is wrong."

## 3. From concept to practice

### 3.1 Specification and analytical calculation

The paper's target is 48 V input, 1 V output, 5 MHz, four phases, four
modules, 1 kW. This corresponds to a total output current of 1000 A; 250 A
average per module; 62.5 A average per phase. Using the paper's
boundary-mode triangular-current approximation, the peak per phase is about
125 A. 5 MHz corresponds to a 200 ns period, the four-phase adjacent
conduction slot is 50 ns, and the theoretical high-side on-time is
16.667 ns.

The analytical audit found one issue that needs confirmation: using the 2024
paper's printed equation, the critical inductance per phase is approximately
1.4667 nH, but Table I gives 2.68 nH. The two values are currently kept as
separate branches: one that checks equation consistency, and one that
strictly preserves the tabulated parameter -- the discrepancy is not removed
by tuning.

### 3.2 Topology and device model

The current model includes a single-module four-phase power stage, three
flying capacitors, four phase inductors, the corresponding high- and
low-side switches, and a common output node.

Information the 2025 paper explicitly provides, and which has been used in
the device-supplement branch, includes:

- High-side switch GS61008T, on-resistance 7 mOhm;
- Low side made of two paralleled GS61008T devices, ideal equivalent
  on-resistance 3.5 mOhm;
- 1EDBx275F gate driver;
- The 2025 prototype uses a 22 nH, 0.5 mOhm inductor, but this value has not
  been transplanted directly into the 48 V P24 main branch;
- The present output capacitor uses an equivalent-capacitance model
  converted from device charge.

Content that has not yet been reliably confirmed includes: the actual switch
model used in P24, the nonlinear output capacitance, the exact equivalent
capacitance participating in each commutation, any added snubber, and the
real dead time and detection delay. At this stage the project can state
which devices the model adopts, but cannot claim to have fully replicated
the authors' hardware.

A second, paper-native device candidate has since been identified: 2024's
own Table 3 (Sec. IV, embedded-package concept) names two parallel
high-side and three parallel low-side EPC2067 GaN switches for exactly this
project's `nP=4`, `nM=4` configuration. This is not confirmed to be the
device Sec. II-B's ZVS mechanism assumes, and no validated on-resistance
figure exists for it in that context, so it is carried as a second,
separately labelled device-sensitivity branch rather than a replacement for
GS61008T (Section 5, item 7).

### 3.3 Commutation path and control

The controller does not force switching at pre-guessed times; it monitors
physical events: the end of the fixed on-time, the inductor current crossing
zero, the negative current reaching its target, and the next high-side
switch's `Vds` reaching zero. Once an event occurs, the gate command must
latch until that stage's exit condition; an instantaneous detection of
`Vds=0` does not mean producing only a momentary narrow pulse.

The current path in the present netlist closes numerically and runs, but
"fully matches the authors' actual circuit" has not been demonstrated. In
particular, the following still need to be checked:

- After the high side turns off, which high- and low-side output
  capacitances actually participate in charging/discharging;
- How the state of the non-active phases' low-side switches changes the
  freewheel path;
- Whether the flying capacitors participate in the commutation energy at the
  next high-side node;
- The low-side reference connection that is not explicitly drawn in the 2024
  figure.

The current conclusion should therefore be stated as "a candidate
commutation path with paper support has been implemented," not "the
freewheel path has been proven correct."

## 4. Two evidence branches

- **P24 branch:** follows the 2024 switching sequence and retains its
  1%-2% peak negative-current condition.
- **P25-to-P24 branch:** extrapolates the 2025 paper's more complete
  operating modes, non-active-phase low-side control, and 5%-10%
  negative-current condition onto the P24 four-phase topology, with the
  extrapolation explicitly labelled.

Both branches share the same top-level boundary: 48 V, 1 V, 5 MHz, single
module, four phases. The current periodic steady-state experiments
uniformly use an ideal 1 V output source to isolate the output-regulation
problem; this is not a zero-start result, nor evidence that the 1 kW system
has been achieved.

## 5. Representative experimental results

1. **Analytical and ideal stage:** reproduced the duty-cycle, on-time and
   125 A peak relationships, while also exposing the inconsistency between
   1.4667 nH and 2.68 nH.
2. **Zero-state startup attempts:** fixed PWM and narrow pulses did not
   reliably self-establish the expected capacitor staircase, and produced
   current accumulation and detection chatter. Zero start is therefore kept
   as a separate, unresolved task and is not mixed with steady-state
   periodic verification.
3. **Local ZVS test:** after adding the GS61008T-equivalent parasitic
   capacitance, P24's 1%-2% negative current did not complete the intended
   ZVS. Sweeping an additional 0-2 nF snubber did not help either -- it
   increased the commutation charge required instead.
4. **Negative-current threshold sweep:** in the local model, 7.76% still
   fails while 7.77% first passes. This only establishes the admission
   threshold of the present local device model; it does not substitute for
   a paper conclusion.
5. **Return to the four-phase system for verification:** putting 7.77% back
   into the complete four-phase controller with every other state held
   fixed, phase 2's high-side `Vds` minimum is still 1.418 V -- ZVS is not
   reached, and the controller correctly halts at this boundary.
6. **A separate, earlier experimental line, using a different method (not a
   continuation of the ratio sweep above):** a hybrid fixed-on-time /
   event-driven controller, solved with an exact two-variable numerical
   search rather than a coarse ratio sweep, shows that a `9%` negative
   current lets phase 2 turn on with its zero-voltage-switching residual
   converged to numerical precision. Applying the identical method one phase
   later, however, shows phase 2's own peak current falls about 7.2 A short
   of the 125 A target, and the subsequent phase-3 event and full
   four-phase period closure still do not pass (the detailed diagnosis of
   that shortfall is in Section 6, item 3).

7. **EPC2067 device-candidate sensitivity:** re-running the full local
   commutation chain with 2024's own Table-3 EPC2067 candidate in place of
   the GS61008T borrowed from 2025 moves the local admission threshold from
   7.76%-7.77% to 22.04%-22.05%, about 2.8x higher. The direction matches
   physical expectation (roughly 9-10x more commutation capacitance needs
   proportionally more negative current), but this candidate's on-resistance
   has not been validated, and Table 3 is Section IV's embedded-package
   concept, not confirmed to be the device Section II-B's mechanism assumes.
8. **Cross-experiment scaling check:** combining three separate local-
   commutation experiments (a snubber sweep and the two device-capacitance
   sweeps above) into one 102-point regression shows the admission threshold
   scales with commutation capacitance close to a simple LC-energy law
   (threshold roughly proportional to the square root of capacitance, fitted
   exponent 0.51+/-0.01, R^2=0.95). This is evidence the mechanism is being
   modeled consistently across a wide range of capacitance assumptions, not
   evidence favoring either specific device.
9. **Real, non-constant device capacitance:** the constant "time-equivalent"
   capacitance used in items 3-8 above is itself an approximation. Digitizing
   GS61008T's own published capacitance-vs-voltage curve and re-running the
   same chain with the real, nonlinear capacitance moves the threshold to
   9.63%-9.64% -- higher, not lower, than the constant-capacitance result.
   The constant value understates the true capacitance near zero volts
   (where this event actually happens) in order to average correctly over
   the full 0-50 V range it is specified for. This directly tests and rules
   out one candidate explanation for why 1%-2% is not reached in this model.
10. **Dead-time feasibility:** replacing the idealized "turn on exactly when
    `Vds` reaches zero" controller with a fixed-delay controller, closer to
    how a real gate driver behaves, shows that catching the natural
    zero-voltage instant is only possible inside a narrow window, about
    0.24 ns wide, centered on the commutation's own natural duration. A
    driver that is too fast or too slow both miss it; past this window, the
    circuit's own ringing (this model has no reverse-conduction clamp)
    produces further, unpredictable near-zero and far-from-zero points
    rather than a safe "long enough is fine" region.

The most important experimental insight is: a single phase's local
commutation passing does not mean the same threshold transfers directly to
the coupled four-phase system. The other phases' currents, flying-capacitor
voltages, and stored-energy state at that moment all change the ZVS outcome.
A second insight follows from items 7-10: two of the most likely candidate
explanations for the gap between the local threshold and P24's stated
1%-2% -- a larger or more realistically-shaped device capacitance, and a
longer switching delay -- have now been tested directly, and neither closes
that gap. Each one that changes the result at all moves it further away,
not closer.

## 6. Current reflections and research questions

1. Is P24's 1%-2% a general control rule, or is it an experimental result
   that depends on specific device charge, dead time, and freewheel path?
2. Is flying-capacitor charge balance in the average sense sufficient to
   guarantee that every individual commutation event has enough energy?
3. Is the difference between 2024 and 2025 regarding the non-active phases'
   low-side switch state one of the reasons the local threshold does not
   transfer to the four-phase model?
   (Supporting evidence, from a separate independent diagnostic experiment
   A39, 2026-09-14): this conjecture already has concrete supporting
   evidence, not just a guess. While investigating why H2's peak current was
   about 7.2 A short of H1's, A39 found that H2's actual current at the
   instant of admission is not set by that phase's own initial-current
   setting; instead it is pinned at about -1.29 A by the physical process of
   `L`-`Coss` resonant commutation (regardless of how that phase's initial
   current is raised or lowered, the admission current itself barely
   changes -- only the admission *time* shifts). This shows that the
   commutation energy each phase actually obtains is determined by the
   coupled state -- including the freewheel path -- not by that phase's own
   isolated setting. If the non-active phases' low-side conduction state
   differs (not explicitly drawn in the 2024 figure; the 2025 three-phase
   prototype has all of them conducting/freewheeling), the freewheel path
   and the device capacitances participating in the resonance change along
   with it, which a local model (typically isolating only two phases) would
   naturally fail to capture. This is fully consistent with, and mutually
   corroborates, A42/A43's finding that "the local threshold (7.76%-7.77%)
   and what the complete four-phase system actually needs (9%) are not the
   same number -- the negative-current fraction is not a topology-
   independent constant."
   (Follow-up, experiment A44, 2026-09-14): A39's pinning claim was tested
   against only one variable, `IL2_INIT`. A44 swept the other six coupled
   state coordinates one at a time to check whether the pinning is real
   against the full state or an artifact of having varied only one of seven
   variables. Four of them -- the other three phases' own starting currents,
   plus the third flying capacitor's voltage -- confirm the same pinning
   (sub-0.01 sensitivity per unit). The first two flying-capacitor voltages,
   `VC1` and `VC2`, do not: moving either one by as little as 0.2-0.5 V does
   not merely shift the admission current, it can eliminate phase 2's
   zero-voltage turn-on event entirely for the whole run. This sharpens
   rather than overturns the earlier claim: H2's admission is immune to the
   other phases' currents but highly sensitive to exactly two specific
   capacitor voltages, consistent with the physical picture that a
   capacitor voltage sets a node's dc bias directly while a current only
   couples in dynamically. This raises a new, currently open question: if
   flying-capacitor voltage precision is this consequential for ZVS, is
   flying-capacitor voltage regulation tolerance an implicit design
   requirement of this topology that the papers do not state numerically?
4. Increasing the negative current improves ZVS margin, but it also
   increases circulating current and conduction loss and disturbs the next
   stage's peak; the negative-current fraction should therefore be a jointly
   optimized quantity, not simply "the larger the better."
5. The present constant-equivalent `Coss` is suitable for mechanism
   screening, but whether it can be used to judge thresholds as close as 1%
   and 2% still needs to be rechecked with nonlinear `Qoss`/`Coss(V)` and
   real drive timing.
6. A runnable periodic trajectory does not by itself show that the circuit
   can enter that trajectory on its own from a zero state. Steady-state
   reproduction and startup strategy must be verified as two separate
   problems.
7. Given that neither a larger/nonlinear device capacitance nor a longer
   switching delay closes the gap toward 1%-2% (Section 5, items 9-10), and
   that the 48 V/1 kW hardware itself was never built, is 1%-2% a general
   property of this topology class established elsewhere in the authors'
   prior work, or specific analytical guidance for this exact configuration
   that depends on an assumption -- a device, a snubber, a different
   commutation mechanism entirely -- this project does not yet have?

## 7. Current bottleneck and next steps

The earliest, reproducible system-level failure point at present is: after
phase 1 establishes its negative current and turns off its low side, phase
2's high side does not reach `Vds=0` before the adjacent time slot, so the
next phase cannot be admitted under the ZVS condition.

The next step should not be to keep blindly increasing the negative current.
Two of the originally planned checks around this boundary have since been
completed directly: a real nonlinear device capacitance (Section 5, item 9)
and a realistic fixed-delay controller (Section 5, item 10) have both been
tested, and neither closes the gap toward 1%-2% -- if anything each moves
the result further away. What remains is:

1. Confirm which device, if either of the two candidates tried (GS61008T,
   EPC2067), the paper's Section II-B mechanism actually assumes, and obtain
   a validated on-resistance figure for it -- neither candidate's conduction
   model is currently confirmed;
2. Determine the real snubber (if any) and the real dead time/detection
   delay -- both remain unconfirmed, and item 10 above shows the required
   timing precision may be much tighter (sub-nanosecond) than originally
   assumed;
3. Verify separately in the P24 and P25-to-P24 branches, then check whether
   the four-phase period closes;
4. Only after the steady-state trajectory is established should the method
   for building the capacitor staircase from a zero state be studied
   separately.

The result at this stage is not a claim that the paper has been fully
reproduced, but that a traceable, replaceable reproduction framework has
been established that can localize the first failure event, narrowing the
problem down to the device commutation, freewheel path, and multi-phase
state coupling immediately before the next phase's ZVS.

## 8. Information requested

The following would let this specific boundary be checked directly, rather
than by further guessing:

1. The real capacitance actually participating in the phase-1-to-phase-2
   commutation -- device `Coss` plus any added snubber -- at the point where
   phase 2's high-side voltage currently stalls before reaching zero. Two
   candidate devices (GS61008T, borrowed from 2025; EPC2067, named by 2024's
   own Table 3) and a digitized nonlinear model for the first have all been
   tried; none reach the stated 1%-2% range (Section 5, items 3, 7, 9), so
   the real value is not something this project can currently narrow down
   further by guessing.
2. Real dead time and gate-driver propagation delay around that same
   handoff. This has sharpened since the last version of this report: the
   zero-voltage-switching window is on the order of 2 ns, and a feasibility
   sweep (Section 5, item 10) shows the window in which a fixed delay
   actually catches that instant is only about 0.24 ns wide -- an order of
   magnitude tighter than "a few nanoseconds" would suggest.
3. The flying capacitors' (`C1`-`C3`) real values, ESR/ESL, and the intended
   voltage-balancing/regulation tolerance -- today's finding that phase 2's
   admission is highly sensitive to `VC1`/`VC2` specifically (Section 6,
   item 3) suggests this tolerance may be a real design requirement, not
   just a modeling detail.
4. Whether EPC2067 (2024's own Table 3 candidate for this exact
   configuration) is the device Section II-B's ZVS mechanism assumes, or is
   specific to Section IV's separate embedded-package concept -- and, if the
   former, a validated on-resistance figure for it, which Table 3 does not
   provide.
