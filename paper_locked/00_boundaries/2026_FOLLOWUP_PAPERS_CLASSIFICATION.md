# Classification of the 2026 follow-up papers (same author line)

## Scope and provenance

Two 2026 papers by the same author group as P24/P25 (Ramin Rahimzadeh
Khorasani and Madhavan Swaminathan appear on both; both explicitly cite the
2024 ECTC paper as [31] and the 2025 APEC paper as [32]) were found
2026-09-14/15 and are classified here per this project's source-coverage
rules. Neither is P24 or P25 itself; both are `CROSS_PAPER_EXTENSION` /
context sources, read for what they say about P24/P25, not as a primary
electrical source for this project's netlists.

- **"A Comprehensive Design Framework for Vertical Power Delivery in HPC"**
  (Krishnakumar, Popryho, Choi, Rahimzadeh Khorasani, Swaminathan, Kumar,
  Partin-Vaisband; arXiv:2606.28837v1, manuscript received 9 May 2026,
  IEEE TCPMT, DOI 10.1109/TCPMT.2025.0000000 placeholder pending final
  publication).
- **"Integrated Vertical Power Delivery -- Review & Challenges"**
  (Swaminathan, Rahimzadeh Khorasani, Partin-Vaisband, Sharma, Kumar; IEEE
  TCPMT, received 26 Feb 2026, accepted 20 Jul 2026, DOI
  10.1109/TCPMT.2026.3716987).

## "Comprehensive Design Framework" -- keyword scan result

Full-text search found **zero** occurrences of "negative current", "ZVS",
"zero voltage", "CCM", "DCM", "dead time", "GS61008T" or "EPC2067", and only
one generic "Coss" mention (a per-area capacitance density,
`Coss0=150 pF/mm^2`, used in a generic GaN switch-loss model "extracted from
... EPC GaN device datasheets", not tied to a specific part or to P24's
mechanism). This paper is a system-level architecture/optimization study
(distributed vertical power delivery, DVPD) comparing single-stage 48V/1V
against two-stage 48V/24V/1V and 48V/12V/1V schemes on efficiency, area,
voltage drop and mechanical/thermal grounds. It does not engage with the
Sec. II-B ZVS commutation mechanism this project is investigating.

**Relevant finding**: single-stage 48V-to-1V (their "Architecture A1") is
still an actively modeled, non-abandoned option as of 2026, reported at 84%
system-wide efficiency at 54% area utilization (up to 87.6% at 75% area,
1-50 kW range) in their DVPD framework. This is a system-level efficiency
estimate from their analytical model, not a claim that 2024's specific
48V/1kW/4-phase circuit was built or measured -- it does not change the
"never built" fact Mihai confirmed 2026-09-15 (see
`CURRENT_ASSUMPTION_CROSSCHECK.md`).

## "Integrated Vertical Power Delivery -- Review & Challenges" -- directly relevant

This paper does engage substantially with our mechanism (27 "ZVS"
occurrences, "CCM"/"DCM", "series capacitor" throughout). Findings relevant
to this project:

1. **Table I** lists a row "2025, Penn State-CHIMES (SRC) [31],[32]: ZVS
   BCM Series-Capacitor Buck (Soft Switched)... 0.5-20 MHz, Nom.: 5 MHz,
   12-48/1, **88.5% (5MHz, 100W, 12V-Vin)**^6... 1.85nH (5MHz)/Discrete-
   Embedded, 6/GaN". Footnote 6 reads: **"Theoretical and simulation
   results."** This is the author group's own 2026 characterization of the
   combined P24+P25 result, and it independently corroborates what Mihai
   told the user directly (2026-09-15): the headline efficiency figure is
   simulated/theoretical, and the quoted operating point is **12V-Vin**
   (matching P25's real prototype voltage), not 48V -- there is still no
   48V-input measured number being cited anywhere, even in this later
   summary. The `1.85 nH` inductance figure does not exactly match either
   of this project's two Table-I-vs-Eq.(4) branches for `nP=4` (`1.34 nH`
   at `nM=2` or `2.68 nH` at `nM=4`); it is closest to the `nM=2` row but
   not identical, and this project does not currently know which exact
   `nP`/`nM` cell the review paper's table intended -- flagged as an open,
   low-priority discrepancy, not resolved here.
2. **Fig. 5** illustrates "a representative three-phase series-capacitor
   buck IVR architecture" for discussing parasitic-loop minimization --
   three phases matches P25's real `nP=3` hardware, not P24's `nP=4`
   concept, consistent with P25 being the only real built circuit in this
   line.
3. **Conclusion, recommendation (c)**: "For high-conversion ratio VRs
   employing series and flying capacitors, current deep-trench capacitor
   technologies are limited to breakdown voltages of approximately 10 V.
   Future development must focus on extending DTC voltage ratings toward
   50 V" -- as of 2026, embedded high-voltage (48V-class) flying capacitors
   remain a stated unsolved integration problem, not an available,
   qualified technology. This is further independent support that a 48V,
   fully-embedded version of this converter is not yet realized.
4. **Conclusion, recommendation (a)**: notes that "for ZVS architectures,
   higher `Psw(on)` switching and `Qoss` parameters are tolerable" compared
   to hard-switched designs -- a qualitative statement (not a number) that
   ZVS operation relaxes the pressure to minimize device Coss/Qoss compared
   to a hard-switched design, offered here only as context, not as evidence
   for or against either the GS61008T or EPC2067 candidate capacitance.

## What this does and does not resolve

Resolves: independently corroborates (from a 2026 primary source, not just
verbal confirmation) that the 48V/1kW case has no measured hardware number,
and that the review paper's own citation of "the" combined P24/P25 result
still reports P25's 12V operating point, not a 48V one.

Does not resolve: which device (GS61008T, EPC2067, or neither) Sec. II-B's
mechanism assumes; any numeric dead time, snubber, or nonlinear Coss(V)
value; or the Table-I-vs-Eq.(4) `1.4667nH`/`2.68nH` discrepancy (the
`1.85nH` figure here is a third, unreconciled number from a different
context and must not be used to adjudicate that discrepancy).
