# Track C - literature behind the multi-module decisions

What each multi-module decision rests on. "Local" means a PDF in the
workspace root (not in this public repo). Entries marked *abstract*
were checked only from the abstract or a search summary, not read in
full.

## 1. One shared voltage loop, one Ton, slaves synchronised to the master (D61 scheme A, C01)

**Why:** boundary-mode modules on one output cannot run independent
integrators (D61). Their periods must be locked actively.

- **Huber, Irving, Jovanović,** "Open-loop control methods for
  interleaved DCM/CCM boundary boost PFC converters," IEEE TPEL, 2008
  (local).
  - Master-slave interleaving of variable-frequency (boundary-mode)
    phases.
  - The slave is delayed by a fraction of the master's measured period.
  - This is the mechanism of our slaves' slots (m T/(M N) from the
    master's measured period).
  - The same paper discusses the current imbalance from inductance
    mismatch under a common on-time.
- **Huber, Irving, Jovanović,** "Closed-loop control methods for
  interleaved DCM/CCM boundary boost PFC converters," APEC 2009 (local).
- **Huber, Irving, Jovanović,** "Review and stability analysis of
  PLL-based interleaving control of DCM/CCM boundary boost PFC
  converters," IEEE TPEL, 2009 (local).
  - The alternative to our open-loop slots; its stability conditions
    apply if a PLL is adopted.
- **"A novel digital control strategy for GaN-based interleaving CrM
  totem-pole PFC,"** 2024 (local; IEEE 10861218): dual-loop
  interleaving with current sharing and small phase error at 500 kHz,
  GaN. A recent confirmation that digital master-slave interleaving of
  boundary-mode phases is practical.
- **"A cross-coupled master-slave interleaving method for boundary
  conduction mode (BCM) PFC converters,"** IEEE (6166383), *abstract*.
- **Context, the master-slave principle for parallel modules** (one
  module regulates, the others follow):
  - "Analysis and design of N paralleled DC-DC converters with
    master-slave current-sharing control" (APEC), *abstract*;
  - "Current sharing and voltage regulation of parallel DC-DC buck
    converters: switching control approach," ISA Transactions, 2023,
    *abstract*.

## 2. Uniform interleave of all M·N phases, and why the 9.44 ns offset mattered (C01 flag, C02 fix)

- **P24 itself** (local, "Package power delivery architecture ... 1 kW
  IVR operated in CCM-DCM boundary mode"): modules and phases
  interleaved to reduce the output ripple. Our uniform T/(M·N) shift is
  the reading of that statement.
- **Roberts' SCB dissertation** (local), and "Modulation improvements
  for high-phase-count series-capacitor buck converters" (local): the
  phases of an SCB are T/N apart. High phase counts are where the
  modulation details matter.
- **"Current ripple cancellation for asymmetric multiphase interleaved
  dc-dc switching converters,"** *abstract*: tolerances and
  asymmetric phase shifts limit ripple cancellation.
  - This is the effect C01 measured: 45.9 A rms against 6.6 A uniform.
- **ADI Analog Dialogue,** "Considerations for the output current and
  voltage ripple in a multiphase buck": the ripple cancellation's
  dependence on N·D and on equal phase shifts. It explains why the
  offset was harmless at 4 phases (N·D 0.31) and costly at 16 (1.22).

## 3. Predicted timing references (dt_pred; the flagged predicted slave reference)

- **"Current zero-crossing prediction-based critical conduction mode
  control of totem-pole PFC rectifiers,"** IEEE TPEL 38(7), 2023
  (local). It predicts the zero crossing instead of waiting for the
  comparator, as our predictive turn-on does.
- **"Cycle estimation-based deadbeat interleaving method for critical
  mode totem-pole rectifiers,"** IEEE TIE, 2024 (local). It interleaves
  from an estimated next cycle.
  - This is the remedy flagged in C02 Section 3: reference the slaves to
    the master's previous low-side turn-off plus the period. It removes
    the latency behind slave 1's late fires.
- **"Interleaving phase shifters for critical-mode boost PFC"** (local),
  and **"A novel closed loop interleaving strategy of multiphase
  critical mode boost PFC converters"** (local): phase-shift generation
  for variable-period phases.

## 4. Current sharing with inductor tolerance (D61, C01)

- **Huber et al. 2008** (above): with a common on-time in boundary
  mode, phase current scales with 1/L. This is D61's relation and C01's
  ±4.7% for ±5% L.
- **"Automatic current sharing mechanism in the series capacitor buck
  converter"** (local): inside one SCB module the series capacitors
  share the phase currents. Between modules there is no such coupling,
  which is why sharing becomes a system problem (P24 calls it "the
  primary challenge").
- **The 2024 GaN CrM interleaving paper** (Section 1): a current-sharing
  loop on top of interleaving. This is the direction of D61's scheme B
  (a per-module trim), which C01 showed needs a per-slave valley target.

## 5. The voltage loop's quantisation limit cycle (Ton toggling in A104/A105/C02)

- **A. V. Peterchev, S. R. Sanders,** "Quantization resolution and
  limit cycling in digitally controlled PWM converters," IEEE TPEL
  18(1), 2003 (local).
  - No limit cycle requires the DPWM (here Ton) resolution to be finer
    than the ADC's, plus integral action.
  - Our Ton LSB moves Vo ~1.8 mV against a 0.5 mV ADC LSB, so Ton
    toggles. Whether it does in a given run depends on where the
    equilibrium falls in the zero bin (C01 and C02 RESULTS).
  - Earlier documents (D59, A104, A105, C01, C02) named this
    "Peterson-Erickson". Corrected 2026-10-02.
- **D. Maksimović, R. Zane,** "Small-signal discrete-time modeling of
  digitally controlled PWM converters," IEEE TPEL, 2007 (local): the
  discrete-time loop model behind D59.

## 6. Not yet covered by literature here

- A system start-up sequence for parallel boundary-mode SCB modules.
  P24 gives none; Intel VRD 11.1's soft-start and Roberts' input ramp
  are the references so far.
- Input feed-forward for fast line steps in boundary-mode SCB modules.
