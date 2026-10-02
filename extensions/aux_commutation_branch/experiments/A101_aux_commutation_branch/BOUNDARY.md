# A101 / D56 - an auxiliary commutation branch for the high side's zero-voltage turn-on (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION` (a topology change that P24 does not have).

**Order of work:**
- D56 (the mathematical model, Sections 3-5) was explored and run before
  this file was written.
- This file registers the co-simulation plan and its predictions
  (Section 7, `d56_predictions.json`) **before any co-simulation code of
  A101.**

## 1. Question

**The high side does not turn on at zero voltage** in any design so far
(scorecard, Section 0).
- It turns on at the resonance valley, about 9 V of the ~12 V it blocks.
- At 5%, D56 estimates that loss at **540 nJ per cycle per phase, 9.3 W for
  four phases** (A91's bounds 3.1-15.9 W).

**Can a small auxiliary branch give the high side zero-voltage turn-on**:
- without raising the main inductor's negative current (its ripple stays
  at the 5% design),
- without losing the low side's zero-voltage turn-on,
- and for less loss than it saves?

## 2. Prior work

**Auxiliary branches for a zero-voltage high-side turn-on:**

| work | branch | what it gives this question |
|---|---|---|
| De Doncker and Lyons, IEEE IAS 1990, DOI 10.1109/IAS.1990.152341 (original ARCP) | Lr and a bidirectional switch from the switch node to the DC-link midpoint | The midpoint at Vdc/2 supplies the energy; the inductor only needs a small "boost" current to cover losses. |
| Hua et al., IEEE TPEL 9(2), 1994, DOI 10.1109/63.286814 (original ZVT) | Lr, auxiliary switch and diode across the main switch | Zero-voltage transition with zero-current auxiliary switching. |
| Adib and Farzanehfard, IEEE TPEL 25(1), 2010, DOI 10.1109/TPEL.2009.2024153 | ZVT with synchronous rectifier | The same idea with a synchronous switch. |
| Nan and Ayyanar, IEEE ECCE 2016, DOI 10.1109/ECCE.2016.7854692 | Lr, a switch and a Schottky diode from the switch node to the output, 1 MHz, 5 V output | Closest structure to a buck. The authors note the diode's conduction loss "limits the use of this circuit for high frequency and high current applications". |
| Musabeyoglu (MIT M.Eng. thesis, 2017; advisors Tilly and Perreault) | a 10-50 nH helper inductor and two helper MOSFETs in a 42 V buck IC | High-side switching loss −45% in simulation (abstract; full text not read, the repository blocked the download). |
| Vicor ZVS Buck white paper (C. R. Swartz) | a clamp switch across the output inductor | Commercial practice: the inductor's own negative current, frozen by the clamp, resonates the node. |
| Ulrich, IEEE APEC 2021, DOI 10.1109/APEC42165.2021.9487229 | clamp switch with an added capacitor (boost) | Extends the ZVS range of the clamp-switch method. |
| Cong et al., IEEE TCSI 66(1), 2019, DOI 10.1109/TCSI.2018.2858544 | one auxiliary branch between two switching nodes | Sharing one branch between nodes. |
| Shen et al., IEEE TPEL 36(12), 2021, DOI 10.1109/TPEL.2021.3085558 | part of the paralleled legs used as an auxiliary leg, with small DM inductors | No extra switches; benefit at partial load (+2.1% at 8% load), worse than synchronous CCM at heavy load. |
| Gong et al., IEEE TPEL 37(3), 2022, DOI 10.1109/TPEL.2021.3114263 | synchronous ARCP with two inductors | Fixed timing wastes energy at light load; variable timing needs detection circuits. |
| Langbauer et al., IPEC-Himeji 2022, DOI 10.23919/IPEC-Himeji2022-ECCE53331.2022.9806882 | ARCP against 3-level TCM | ARCP auxiliary transistors switch on at zero current but hard (Coss loss); timing limits ARCP at high frequency; optimal auxiliary chip area. |
| Lehmeier et al., IEEE APEC 2024, DOI 10.1109/APEC48139.2024.10509084 | ARCP with one inductor shared by three phases | Variable timing; about −50% loss at 30 kHz. |
| Amini, Berger, Hengstenberger, WO2023168514A1 (priority 2022-03-03) | ARCP | The DC-link capacitors are balanced by lengthening the auxiliary charging interval. |

**What none of them covers:** a filter inductor as small as the resonant
inductor. P24's Lf is 1.47 nH, and D56 shows this changes the
requirement completely (Section 3).

## 3. The physics: the filter inductor sets a floor

**The model.** During the rising edge the node sees two inductors in
parallel:
- Lf to Vo, and
- Lr to the branch's source Vs.

With a linear capacitance C:

    x_max = V_th + sqrt(V_th^2 + (Z_eq I_0)^2),
    Z_eq = sqrt((Lf || Lr) / C),
    V_th = (Lf || Lr) (Vo / Lf + Vs / Lr)

**Read the expression this way:**
- **With the branch at 0 V or at Vo** (Nan and Ayyanar, a clamp switch, a
  branch between switch nodes):
  - V_th is about 1 V and Z_eq ≤ sqrt(Lf / C) ≈ 0.36 Ω.
  - So the total current at the turn-off must still be about 33 A,
    whatever Lr is.
  - The branch only moves the current that raising the negative current
    would provide.
- **With Vs above half the rail and Lr ≤ Lf,** V_th approaches Vs and the
  node swings to the rail with no extra current. This is the ARCP
  midpoint's role.

**D56's nonlinear model confirms it** (phase 1, i_neg 6.25 A):

| branch | Lr | auxiliary current needed at the turn-off |
|---|---|---|
| to Vo (1 V) | 0.25-10 nH | 82-29 A |
| to a source at Vm | 0.5 nH, Vm ≥ 8 V | 0 A |
| to a source at Vm | 0.25 nH, Vm ≥ 7 V | 0 A |
| to a source at Vm | 1 nH, Vm 7-9 V | 22-5 A |

**Structures dropped:**
- **The branch to Vo:**
  - It draws 0.85-4.3 µC per cycle from the 1 V output.
  - That is 3.5-19 A of extra average current per phase.
- **An auxiliary leg from the phase's own high-side rail (Shen):**
  - In the series-capacitor chain that rail is a floating node.
  - The leg would need its own series capacitor, which no current
    balances.
- **A branch between switch nodes (Cong):**
  - The other nodes are at 0 V at each turn-on (duty 1/12, four phases),
    so V_th stays about 1 V.

## 4. The chosen structure: a bidirectional switch to a self-balanced Cm

**Per phase:** Lr and a bidirectional switch (BDS, two dies in common
source) from the switch node x_k to a capacitor Cm to ground.

**Sequence:**
1. **The BDS turns on with the low-side turn-off.**
   - Its current starts at zero.
   - It is a hard turn-on at V_DS = Vm, a Coss loss scaled by the die
     area.
2. **Rising edge.** Lr drives x to the rail; the high side turns on at
   zero voltage.
3. **During the high side's on-time,** Lr sees Vm − V_rail < 0. Its
   current falls through zero and recharges Cm.
4. **At the high-side turn-off,** the negative branch current adds to the
   falling edge. This helps the low side's zero-voltage turn-on; the
   low-side dead time is shortened.
5. **After the low-side turn-on,** Lr sees +Vm. Its current returns to
   zero and the BDS opens at zero current.

**Cm's charge over the cycle sets Vm.**
- The charge drawn per cycle rises with Vm, so the equilibrium is stable
  and Cm self-starts.
- **This differs from the ARCP patents:**
  - no DC-link midpoint;
  - no balancing control;
  - the main ripple is unchanged, because the branch's net charge into
    the node is zero and the high side turns off at the same inductor
    peak current.

## 5. D56 - the mathematical model and its results

**Model:** `src/scb_ivr/p24_aux_commutation.py`.
- **Physics:** one switch node with:
  - the EPC2067 Coss(V) of 2 high-side, 3 low-side and the next phase's
    2 high-side devices;
  - Lf; the branch; reverse conduction.
- **Validation:** against the full four-phase nonlinear model.
  - Phase 1's valley for i_neg 6.25-37.5 A: within 0.034 V.
  - The four phases at the 5% orbit: within 0.05 V and 0.04 ns, once
    each series capacitor's charge from the previous phase's on-time
    (≈0.40 V) is included.
- **Run:** `scripts/p24_aux_commutation.py`. Output:
  `symbolic_derivations/03_P24_native/diagnostics/D56_aux_commutation_5p0pct.json`.
  Tests: `tests/test_p24_aux_commutation.py` (6).

**Assumed values (none from P24):**
- BDS dies of alpha × EPC2067:
  - 2 × 1.3 mΩ / alpha;
  - QG 17.1 nC × alpha at 5 V;
  - Coss × alpha.
- Lr's resistance 0.2 mΩ.
- Turn-off current fall 0.5-1 ns, for the overlap bracket.

**Loss bookkeeping per cycle, against the same model without the
branch:**
- the saved hard turn-on;
- branch conduction;
- extra high-side and low-side conduction;
- dead-time reverse conduction;
- BDS gate charge (two dies, once per cycle);
- BDS Coss at turn-on and after the opening;
- the high side's larger turn-off current, as an overlap range.

**Phase 1, retuned low-side dead time, best alpha per Lr; powers for four
phases:**

| Lr | Vm* | alpha | high-side V_DS at turn-on | branch current | high-side turn-off current | net (central) | net with A91's lower / upper bound |
|---|---|---|---|---|---|---|---|
| none | - | - | 8.96 V | - | 134.6 A | 0 (9.31 W hard turn-on) | - |
| 0.50 nH | 9.58 V | 0.4 | 0 | +44 / −45 A | 179 A | −3.2 to −3.8 W | +2.3 / −10.5 W |
| **0.75 nH** | **9.06 V** | **0.3** | **0** | **+33 / −37 A** | **171 A** | **−4.5 to −4.9 W** | **+1.2 / −11.7 W** |
| 1.00 nH | 8.61 V | 0.25 | 1.0 V | +26 / −32 A | 166 A | −5.1 to −5.5 W | +0.6 / −12.1 W |
| **1.25 nH** | **8.26 V** | **0.25** | **2.15 V** | **+22 / −28 A** | **162 A** | **−5.2 to −5.5 W** | **+0.3 / −11.8 W** |
| 2.00 nH | 7.68 V | 0.2 | 4.24 V | +15 / −20 A | 155 A | −4.7 to −4.9 W | −0.1 / −9.9 W |

**The main terms at 0.75 nH** (nJ per cycle per phase):

| term | nJ |
|---|---:|
| saved | −540 |
| branch conduction | +110 |
| gate | +51 |
| BDS Coss | +55 |
| high-side conduction | +25 |
| turn-off overlap | +9 to +34 |

**Per phase, as registered** (`d56_predictions.json`):
- Four-phase net −4.1 to −4.5 W at 0.75 nH, −4.9 to −5.2 W at 1.25 nH.
- Vm* is 9.06-9.45 V and 8.28-8.68 V; phase 4 has no next high side.

**Readings:**
1. **Whether the branch pays depends on the hard turn-on loss.**
   - With D56's central estimate it saves about 5 W, 2% of the output.
   - With A91's lower bound (Eoss of the high side alone) it loses up to
     1-2 W.
   - The central estimate is the standard hard-switching charge loss
     (the device's own Eoss plus the other capacitances charged through
     its channel); the lower bound omits the second part.
2. **Full zero voltage is not the optimum.** The branch's cost grows with
   its current; 1.0-1.5 nH, with a 1-3 V valley, saves slightly more than
   0.75 nH.
3. **The low side keeps zero voltage in every case.**
   - The falling edge is faster.
   - With the old fixed dead time (1.26 ns) the low side conducts in
     reverse at about 2.4 V: +4 to +62 nJ.
   - Retuned to the same turn-on voltage (−0.69 V), the dead time becomes
     0.97-1.11 ns and that loss is zero.
4. **Timing is tolerant:**
   - **BDS turn-on ±1 ns from the low-side turn-off:**
     - 0.5-0.75 nH: zero voltage kept;
     - 1-2 nH: V_DS changes by ≤ 0.66 V.
   - **High-side turn-on at 0.75 nH:**
     - early by 0.5 / 1 ns: +3 / +16 nJ;
     - late by 1 ns: 0.
   - The RTL resolution is 31.25 ps; the jitter studied is 30-100 ps.
5. **The high side turns off at 155-180 A instead of 135 A.** Its turn-off
   overlap is priced as a range; the device's pulsed rating is 409 A per
   die.

## 6. Co-simulation plan (all opt-in; gates bit-identical with it off)

### 6.1 Plant (circuit.py, plant_kernel.c, plant.py, bridge.py)

**cfg key `aux`** = {lr_nh, alpha, r_lr, cm_uf, vm0, phases}:
- **Per phase:**
  - a node m_k with Cm to ground;
  - a branch current i_r,k through Lr from m_k to x_k, in series with the
    BDS resistance 2 RDS(on) / alpha when on.
- **The BDS opens at the first zero of its current after its
  off-command.** This is ideal zero-current detection, an assumption
  priced in Section 8.
- **BDS Coss is not in the plant;** it is priced in the bookkeeping, as in
  D56.

### 6.2 RTL (scb_phase.v)

**`cfg_aux`:**
- the BDS on-command with the low-side turn-off command;
- its off-command with the low-side turn-on command.

**The high side's turn-on.** With the branch the node reaches the rail
and then sits at the reverse-conduction clamp, so there is no valley.
1. **First:** check whether the existing predictive turn-on and A92's
   corrector (`eh_tgt_ps`, the early/flat flags) converge to the rail
   instant.
2. **If not:** use the existing high-side V_DS ≤ 0 comparator (`cmp_zh`)
   to time it, as a measured option.

**Low-side dead time:** set to D56's retuned values, through the existing
low-side corrector or its target.

### 6.3 Gates

- `--full` regression bit-identical;
- the 13-orbit gate;
- unit tests;
- synthesis.

### 6.4 Runs

| run | aux | purpose |
|---|---|---|
| ref | none | the adopted design (A97), the comparison |
| z075 | Lr 0.75 nH, alpha 0.3, Cm 1 µF from 0 V | full-zero-voltage design |
| p125 | Lr 1.25 nH, alpha 0.25 | partial design |
| z075_j30 | z075 with 30 ps jitter | timing robustness |

At most 4 at a time.

## 7. Registered predictions (`d56_predictions.json`)

**Criteria, per phase, over the last 200 cycles:**
1. **Vm:** within ±0.4 V of D56's Vm*.
2. **High-side turn-on V_DS:**
   - z075: ≤ 0.5 V on every phase;
   - p125: within ±0.5 V of D56's 2.0-2.2 V.
3. **Branch current extremes:** within ±20%.
4. **High-side turn-off current:** within ±12 A of D56's 162-172 A.
5. **Low side:** turn-on V_DS ≤ 0 V on every phase (zero voltage kept);
   no overlap.
6. **Inductor ripple:** each phase within ±3% of the reference run.
   **The 5% design is unchanged.**
7. **Vo mean:** within ±5 mV of the reference run.
8. **Phase average currents:** within 1.5 A of the reference run.
9. **Start-up:** Cm self-starts from 0 V and settles within 2% of its
   final Vm.

## 8. Assumed absolute values the conclusion depends on

For Mihai, or for public data:
- **The hard turn-on loss model (the decisive one).** D56's central
  estimate against A91's bounds. A measured or simulated P24 loss
  breakdown would settle it.
- **The BDS:**
  - which device (α-scaled EPC2067, though a ~12 V part would do);
  - its gate supply, which must float with the switch node;
  - its zero-current detection.
- **Lr of 0.75-1.25 nH and Cm of about 1 µF per phase in the package:**
  the area and the parasitic inductance of the loop.
- **The turn-off fall time** used for the overlap range.
- **P24 states that 1-2% negative current is enough.** If its node
  capacitance or a snubber differs from this model, the 540 nJ, and
  everything here, scales with it. This is the existing open question.
