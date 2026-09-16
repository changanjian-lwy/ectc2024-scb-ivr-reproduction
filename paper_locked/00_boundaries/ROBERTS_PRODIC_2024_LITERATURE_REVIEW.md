# Roberts & Prodić 2024 (OJPEL) literature review - outcome (2026-09-16)

## Why this review was required

`paper_locked/02_ectc2024_main/STEP_06_R02_LITERATURE_STARTUP_MODULE.md`
("Next hard gate - PWM takeover") explicitly blocked combining any
precharge/startup module (R02A/B/C, or this session's Track-B zero-start
extension) with the P24 four-phase switching stage until the
four-phase/high-phase-count modulation paper P25 directly cites was
reviewed, "to avoid inventing the four-phase release sequence":

Gianluca Roberts and Aleksandar Prodić, "Modulation Improvements for
High-Phase-Count Series-Capacitor Buck Converters," IEEE Open Journal of
Power Electronics, 2024, DOI `10.1109/OJPEL.2024.3417017`.

This review was performed 2026-09-16 by reading the full 22-page published
article (user-provided PDF, not just the abstract) and searching its
complete text for every startup/precharge/bootstrap-related term.

## Finding: this paper does not contain a four-phase startup/release
   sequence, and cannot satisfy the STEP_06 gate as originally hoped

**The paper's actual subject is a STEADY-STATE modulation technique
("Phase Activation Sequences," PHACTS / "star sequencing"), not a
startup or zero-energy-precharge sequence.** Direct quotes from the
paper:

- PHACTS are defined as directed Hamiltonian graphs where "traversal
  between nodes occurs every `Tsw/N` seconds" (`Tsw`=switching period) --
  i.e. a REPEATING, ALREADY-PERIODIC phase-activation order used once the
  converter is already switching at steady state, used to extend the
  maximum achievable input-to-output conversion ratio beyond the
  conventional `1/N^2` limit (`N`=phase count) without added switch
  voltage stress.
- Directly relevant to this project's own 4-phase case, the paper states:
  "In configurations with `2<=N<=4` equally-separate phases, there exists
  no such phase activation sequence (PHACTS) that allows all main-switch
  duty ratios to exceed (1)... none of the following PHACTS: `{1,2,3,4}`,
  `{1,3,2,4}`, `{1,3,4,2}`, etc., permit the main-switch duty ratios of a
  4-inductor SCB to extend past 25%." **PHACTS provides no benefit at
  all for `N=4` (this project's own phase count) -- the technique only
  produces a conversion-ratio improvement for `N>=5`.**
- A full-text search of all 22 pages for `start-up`, `startup`,
  `precharg(e/ing)`, `bootstrap`, `zero-energy`, `zero-state`, `energiz*`,
  `initial condition`, and `power-up` found: every "energization" hit
  refers to steady-state per-cycle inductor current buildup during normal
  switching (e.g. "the energization of each inductor occurs..."), not a
  from-zero-energy startup transient; the single "bootstrap" hit refers to
  "conventional cascaded bootstrap circuits" -- ordinary high-side
  gate-driver bootstrap supply circuitry, an unrelated standard term, not
  converter startup; the single "initial condition" hit refers to
  iteration `n=0` of an unrelated large-signal-averaging numerical solver
  used for a different modulation technique (MDI current-balancing),
  denoting a solver's own starting iterate, not the converter's physical
  startup state. **No discussion of capacitor precharging, zero-energy
  bootstrapping, or a startup release sequence exists anywhere in this
  paper.**

## Consequence for the STEP_06 gate and Track-B zero-start work

The STEP_06 gate's premise -- that this specific citation would supply an
authoritative four-phase release/handoff sequence -- **does not hold**.
This is not a failure of this review; it is a genuine, now-confirmed
finding that the citation P25 makes to this paper is for an unrelated
purpose (steady-state conversion-ratio/DPWM-resolution extension, cited
by P25 for THAT reason), not for startup sequencing. No other paper in
this project's currently-reviewed source set (P24, P25, EPE2019, IPEC
2018, APEC 2016) has been found to supply an explicit four-phase
zero-energy startup/release sequence either (`STEP_06`'s own "Reference-
chain audit before R02C" section already noted "Neither P24 nor P25
provides or directly cites an exact four-phase startup circuit").

**Therefore: any four-phase release/handoff sequence used in this
project's own precharge-to-PWM work (R02C's own three-independent-branch
extension, or any future Track-B handoff experiment) remains, and must
continue to be labelled, an explicit engineering hypothesis of this
project's own construction (`NUMERICAL_IDEALIZATION`/
`CROSS_PAPER_EXTENSION`-adjacent), not a literature-derived rule.** This
does not lift STEP_06's own caution about "inventing" a release sequence
-- it means that caution must now be satisfied by explicit, documented,
labelled engineering justification within this project rather than by a
literature citation, since no reviewed source supplies one. R04E9-R04E14
already follow this discipline (every admission-order/timing construct in
that lineage is explicitly labelled `SENSITIVITY_ONLY`/
`NUMERICAL_IDEALIZATION`, never claimed as paper-derived); this finding
confirms that discipline was correctly conservative and should continue
unchanged for any future precharge-to-PWM handoff experiment.

## What this review does not establish

- It does not review Roberts' own PhD dissertation ("Multiphase Hybrid
  Switched-Capacitor Buck Converters: Synthesis, Packaging, Modelling,
  and Control for HPC Applications," University of Toronto), which may
  contain additional material beyond this journal article -- not
  reviewed here; if obtained later, it should be checked independently
  rather than assumed to share this article's negative finding.
- It does not review any other paper for a four-phase startup sequence --
  only this one specific, previously-gated citation.
- It does not change any existing experiment's results or grading; it
  only resolves the literature-review prerequisite `STEP_06` itself
  raised, with a negative (source-does-not-apply) outcome.
