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

- It does not review any other paper for a four-phase startup sequence --
  only this one specific, previously-gated citation.
- It does not change any existing experiment's results or grading; it
  only resolves the literature-review prerequisite `STEP_06` itself
  raised, with a negative (source-does-not-apply) outcome for THIS
  specific paper's PHACTS technique.

## Follow-up (2026-09-16, same day): Roberts' PhD dissertation DOES
   contain a directly relevant start-up mechanism -- a DIFFERENT one
   from anything this project's Track-B lineage has tried

The user separately obtained and provided Roberts' PhD dissertation,
"Multiphase Hybrid Switched-Capacitor Buck Converters: Synthesis,
Packaging, Modelling, and Control for HPC Applications" (University of
Toronto, 2025, 244 pages). A full-text search and close reading of
Chapter 3, Section 3.5 ("Converter Start-Up," pp. 62-66 of the thesis's
own numbering) found a genuinely relevant, well-developed start-up
mechanism -- distinct from `star-sequencing`/PHACTS (confirmed, via the
same full-text search, to be exclusively a steady-state, `N>=5`-only
modulation technique with zero relevance to start-up, reconfirming this
document's earlier finding against the published journal article).

**The mechanism (verbatim/close-paraphrase of Section 3.5):**

- "Prior to being turned-on, all converters start off with their reactive
  components being completely de-energised... all inductors initially
  have zero current and all capacitors have zero voltage." If Vin is
  suddenly applied at full value without the FCs pre-charged, "upon the
  first activation of `QMS1`, `QSR1` will end up blocking the full
  input-voltage... if the switches were designed to withstand only [the
  nominal nP-derived blocking voltage] there would be an instant
  catastrophic failure." This directly matches this project's own R03A
  finding (fixed-PWM hard-start produces current runaway) and the
  general physical concern this project has documented since R00.
- **The proposed fix is neither an independent passive-divider precharge
  network (R02A/B's own approach) nor an active per-phase current-limited
  admission sequence (this project's own R04E9-R04E14 lineage). It is: 
  ramp `Vin` itself slowly and controllably through an eFuse, while the
  converter's own normal gate-drive/PWM pattern is either already active
  from the start, or begins once the ramp reaches some fraction of its
  final value** ("another realistic scenario might have the gating
  signals toggling only once the input ramp has reached a certain low
  value relative to its final destination (e.g., 5 V on its way to
  48 V)"). The flying capacitors are NOT independently precharged by a
  separate network; they are brought up organically, in proportion, by
  the SAME charge-balance mechanism that holds them at their nominal
  ratios in steady state, simply because `Vin` itself is rising slowly
  enough for that mechanism to track it.
- **An explicit, quantitative design rule for the ramp rate** is given:
  use the ramp's `10%-90%` rise time to estimate its spectral bandwidth
  (Appendix B), and choose that rise time long enough that the ramp's
  bandwidth sits well below the flying-capacitor resonant frequency (the
  same `LCfly` resonance this dissertation's own Section 3.4 derives
  analytically for `N=2,3,4,...`-inductor SCBs, Eq. 3.44). Worked example
  (2-inductor SCB): FC resonance `~65.7 kHz` -> a bandwidth-matching rise
  time of `~5.3 us` -> multiplied by a `30x` safety margin to `160 us` ->
  total ramp time `200 us`. The dissertation's own simulated comparison
  (Fig. 3.12, `Vin=5 V`, `Vout~0.8 V`, `L=120 nH`, `C1=10 uF`,
  `Cout=100 uF`, `fsw=500 kHz`) shows hard-starting produces switch
  overvoltage while this soft-start ramp does not.

**Why this is a genuinely new candidate for this project's own Track-B
work, not a restatement of anything already tried:**

- It is NOT R02A/B's passive-divider-plus-diode network (that network has
  no counterpart in Roberts' own described mechanism at all -- his FCs
  charge via the converter's OWN active switching action tracking a slow
  Vin ramp, not via an independent resistive/diode divider path).
- It is NOT R04E9-R04E14's admission-order/timeout-gated inductor-mediated
  charging construct (those keep `Vin` at its full, final value throughout
  and instead gate WHICH phase is switching WHEN; Roberts' mechanism keeps
  the normal multi-phase switching pattern conceptually unchanged and
  instead ramps `Vin` itself).
- It comes with an explicit, derivable design rule (ramp bandwidth vs. FC
  resonance) rather than being a numerically-swept sensitivity axis with
  no first-principles justification -- this project's own Section 3.4
  chapter (Eq. 3.44) gives the exact `N`-inductor FC-resonance formula
  needed to compute the equivalent bandwidth target for P24's own
  `N=4` case.
- It is authored by the SAME researcher (Roberts) whose EPE2019 paper is
  already the source of this project's (corrected) `Cfly` provenance
  history, and whose OJPEL 2024 paper P25 directly cites -- i.e. this is
  the most directly author-linked candidate mechanism found so far, even
  though the specific citation P25 makes (PHACTS) does not itself cover
  start-up (Section "Finding" above).

**What this does NOT establish:**

- The dissertation's own worked example is for a 2-inductor, 5 V SCB, not
  P24's 4-inductor, 48 V configuration -- the `200 us` ramp time and
  `30x` margin are illustrative, not directly transferable numbers; P24's
  own `Cfly`/`Lphase`/`Vin` values would need to be substituted into
  Eq. 3.44 and Appendix B's bandwidth relation to derive a P24-specific
  ramp-time target.
- Section 3.5 does not specify an exact `N=4` gate-timing/handoff rule
  beyond the general soft-start principle -- unlike PHACTS, it is not a
  discrete combinatorial sequence table, but a continuous ramp-rate
  design criterion applicable to any `N`.
- This mechanism has NOT been built or tested in this project's own SPICE
  model. It is a documented, primary-source-confirmed candidate
  direction, not a validated result -- any future experiment implementing
  it must derive its own P24-specific ramp-rate target from Eq. 3.44
  (labelled `CROSS_PAPER_EXTENSION`, since it borrows Roberts' own
  dissertation's general method applied to a specific operating point
  neither he nor P24/P25 numerically worked out) and test it in LTspice
  before any claim of feasibility is made.
- It does not resolve whether this mechanism is what P25's own real,
  measured 12 V/200 W hardware actually used at start-up -- P25 itself
  does not describe its own start-up procedure (per this project's
  existing boundary notes); this is Roberts' own general-purpose SCB
  design guidance from his dissertation, not a confirmed statement about
  P25's specific prototype.
