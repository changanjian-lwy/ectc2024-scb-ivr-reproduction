# Paper-locked reproduction baseline

## Rule of use

The 2024 ECTC paper defines the 48 V/1 V, 1 kW architecture, Table I targets
and its three phase-local operating intervals. The 2025 APEC paper supplies
detailed SCB commutation modes only where they do not contradict that P24
sequence, plus the demonstrated 12 V/1 V hardware. A value enters the main model only when
it is (a) printed in one of these papers, (b) calculated directly from a
printed equation, or (c) visibly labelled as an unresolved model variable.
The earlier I0 simulations are numerical diagnostics, not parameter sources.

## Method-selection and failure boundary

1. A topology, control law, startup sequence, stopping condition or parameter
   may enter an experiment only when its provenance is stated in the netlist
   header and experiment record.
2. P24 and P25 are joint primary sources for this project: P24 defines the
   target architecture and analytical case, while P25 may supply circuit-level
   implementation detail. Neither paper automatically overrides the other.
   When they conflict, both branches remain visible and the user selects the
   branch before it enters a primary simulation. Their cited literature comes
   next, followed by other directly relevant literature and finally a clearly
   labelled sensitivity assumption. A sensitivity assumption is never promoted
   to a paper value.
3. A useful idea from another topology may be implemented as a detachable
   functional module only after its non-equivalent connections and limitations
   are listed. It must not silently modify the locked P24 power stage.
4. Numerical success, agreement with a target voltage, or an attractive plot
   never authorizes changing a boundary or hiding an omitted physical mode.
5. Failed experiments remain indexed with the changed variable, failure time,
   solver/electrical symptom, conclusion and next allowed action.
6. Generated raw/database files from aborted or non-interpretable runs may be
   deleted after the failure is captured in the written record. Netlists and
   useful logs are retained so the failure remains reproducible.

## Mandatory P24 pre-run and pre-report gate

Before generating a new primary netlist, starting LTspice, or reporting a
result as progress toward reproduction, answer all five checks in its record:

1. **Topology:** Is every power connection supported by P24 and/or clarified by
   P25, with the exact source recorded and any disagreement exposed?
2. **Conducting set:** Does every simultaneous switch combination follow the
   combined P24/P25 operating description? An ordinary buck complementary rule
   is prohibited unless the papers produce the same state.
3. **Transition boundary:** Is every stage ending condition printed in P24 or
   P25, and has any conflicting value been presented to the user for selection?
4. **Parameter provenance:** Is every number P24-derived, P24-printed, a named
   conflict branch, or an explicitly labelled cross-source sensitivity value?
5. **Claim boundary:** Does the planned conclusion exclude startup, ZVS,
   hardware, loss or balance claims not exercised by the model?

If any answer is `no` or `unresolved`, the primary run is blocked. The next
action must be source transcription or a separately named exploratory test,
never an inferred conventional control law.

## Published topology and timing

| Item | Paper basis | Main-model treatment |
|---|---|---|
| Series-connected high-side ladder, flying capacitors, grounded low sides, one output inductor per phase | 2024 Fig. 3; 2025 Fig. 1 | Fixed topology |
| Phase interleaving | 2024 Sec. II-B; 2025 Figs. 1-2 | Phase shift `T/nP` |
| Module interleaving | 2025 Sec. II: modules shifted by `360/nM` | Module shift `T/nM`, not the earlier invented `T/(nP*nM)` convention |
| High-side on-time | 2024 Eq. (1), Table I; 2025 Eq. (17) | `D=nP*Vo/Vin`, `Ton=D/fsw` |
| P24 interval 1 | 2024 Sec. II-B | `QH1` and `QS2` conduct; `iL1` rises |
| P24 interval 2 | 2024 Sec. II-B | `QH1` turns off; positive `iL1` commutates high-/low-side Coss; `iL1` reaches zero |
| P24 interval 3 | 2024 Sec. II-B | same-phase `iL1` reaches 1%-2% negative; `QL1` turns off and `QH1` returns to ZVS |
| P25 Mode 1 | 2025 Fig. 3 and Eqs. (1)-(4) | Supplement for otherwise-unspecified non-active low-side freewheel states |
| P25 Mode 2/2' | 2025 Fig. 3 and Eqs. (5)-(6) | Supplementary CH/CL submode equations; numeric timing remains missing |
| P25 Modes 3-6 | 2025 Fig. 3 and Eqs. (7)-(16) | Cross-phase handoff candidate; not automatically merged into P24 interval 3 because its boundary follows `iL2` and uses a different negative-current range |
| Current sensing | 2025 Sec. III | One representative inductor current per module; not one detector per phase |
| Control family | 2025 Table IV | Adjustable on-time and off-time / constant off-time; the exact controller circuit is not published |

## Published numerical targets

### 2024 ECTC analytical case

- `Vin=48 V`, `Vo=1 V`, `Po=1 kW`, `nP=4`, `nM=4`, `fsw=5 MHz`.
- From Eq. (1): `D=4/48=0.083333`, hence `Ton=16.667 ns`.
- From Eq. (2): `IL,pk=2*1000/(4*4)=125 A`.
- Table I prints `Lcrit=2.68 nH` for this row, while printed Eq. (4) and the
  locked inputs give approximately `1.4667 nH`.
- User decision: the main model uses the recalculated `1.4667 nH`; `2.68 nH`
  remains only as a documented table inconsistency and is not a simulation
  branch or parameter candidate.

### Table I / Eq. (4) discrepancy: per-`nP` structure (rechecked 2026-09-14)

The `table/Eq.(4)` ratio at 5 MHz is not a single approximately-constant
factor; it is essentially exact within each `nP` group (all `nM` sub-rows of
a given `nP` agree with each other to within Table I's own printed rounding)
but differs sharply between `nP` groups:

| `nP` | `table_L / Eq.(4)_L` at 5 MHz (all `nM` rows) |
|---:|---:|
| 4 | ~1.827-1.841 (not a clean small integer) |
| 6 | 2.000 (exact) |
| 8 | ~1.995-2.003 (matches `2x` within Table I's printed rounding) |
| 16 | ~1.000-1.003 (matches `1x`, i.e. agrees with Eq. (4) directly) |

Three of the four `nP` groups (6, 8, 16) match a clean integer multiple of
the Eq. (4) prediction (`2x`, `2x`, `1x` respectively) essentially exactly.
The `nP=4` row — the row this project's active mainline uses — is the one
group that does **not** fit either clean multiple; it sits at an
intermediate, non-clean ~1.83x that does not resolve to a simple factor.

This pattern is evidence against a single hidden alternate formula applied
uniformly across Table I (a uniform formula would not produce clean integer
multiples for three groups and a non-integer multiple for the fourth). It is
more consistent with an inconsistent, per-row table-generation or
spreadsheet-transcription error, one of the causes this document already
listed as unresolved. This does not change the adopted `1.4667 nH` value or
promote `2.68 nH` to a candidate; it only sharpens the discrepancy record for
any future correspondence with the authors, and it must not be used to infer
a "correction factor" applied back onto `nP=4`.

This ratio table has since been independently re-derived directly from
freshly extracted primary-source Table 1 text (not a prior recalculation) in
`TABLE1_PRIMARY_SOURCE_EXTRACT.md` (2026-09-14), which also confirms this
project's own `nP=4` raw inputs (`Vin`, `Vo`, `nP`, `nM`, `fsw`, `Ton`,
`IL,pk`, table `Lcrit`) match the printed cell exactly, ruling out a
project-side transcription error as the cause of the discrepancy.
- 2024 Sec. II-B asks for approximately 1-2% negative peak current before
  low-side turn-off.

### Mandatory ideal/device-layer separation

The 2024 `125 A` value is a lossless analytical target. It is tested directly
only in the `P24_IDEAL` layer defined by
`EXPERIMENT_PROTOCOL_AND_ARCHIVE_RULES.md`. When P25's GS61008T
`RDS(on)=7 mOhm` or other non-ideal device data is electrically active, the
experiment is `P25_DEVICE_AUGMENTED`: it must calculate the phase-local RL
endpoint from the actual admission current and available drive voltage, and
must report that endpoint residual separately from the difference to the
2024 ideal `125 A` reference. A lower non-ideal endpoint alone is not evidence
that the P24 topology or Eq. (2) has failed.

The model layer does not resolve the separate sequence conflict: the P24
1-2% branch and P25 5-10%/9% extensions remain separately labelled.

### 2025 APEC demonstrated hardware

- `Vin=12 V`, `Vo=1 V`, `Po=200 W`, `nP=3`, `nM=3`, `fsw=0.5 MHz`.
- Table II prints `D=0.26%`; Eq. (17) requires a dimensionless duty near
  `0.25`, and the notation is therefore internally ambiguous/likely a percent
  typo. It must not silently become an exact controller setting.
- Each module supplies about `67 W`; measured phase peak current is about
  `50 A`; measured module ripple is about `15 A`.
- High-side: GS61008T, printed `RDS(on)=7 mOhm`.
- Low-side: two parallel GS61008T devices per phase.
- Inductor: Coilcraft 1212VS-22N, `22 nH`, printed `RDC=0.5 mOhm`.
- Gate driver: Infineon 1EDBx275F.
- Series-capacitor family: `GRM32EC72`; output-capacitor family: `GRM219R60`.
  The paper omits the suffixes and therefore does not identify capacitance,
  voltage rating, tolerance, ESR or ESL.
- 2025 operating-mode text uses 5-10% negative peak current; Sec. III and Eq.
  (20) use up to 5%. These are separate validation cases, not one hidden
  chosen threshold.

## Missing values that block a unique device-level reproduction

- Full Murata capacitor part numbers and populated quantities.
- Values of `CH1...CH3` and `CL1...CL3`; the paper only states that added
  snubber capacitance is used.
- Actual dead times and gate-driver propagation/skew settings.
- Exact zero-cross detector circuit, threshold, filtering and blanking. The
  paper points to reference [22] rather than publishing the implementation.
- Startup/precharge sequence and initial capacitor voltages.
- PCB/package parasitics and nonlinear GaN capacitance model used in any
  simulation behind the paper figures.

These items must remain named variables or questions for the authors. A run
that assigns them guessed values is a sensitivity experiment, not the main
paper reproduction.

The active Track-A capacitance implementation keeps these roles separate in
`GS61008T_commutation_capacitance.lib`: device Coss is populated from the
external GS61008T data module, while unpublished added snubbers default to zero.
The current threshold remains a separate P24/P25 control branch and is never
obtained by fitting the capacitance.

## Lessons retained from the earlier simulations

1. LTspice's default inductor series resistance must never be left implicit;
   every run declares it explicitly.
2. A completely lossless zero-energy switched LC network can retain undamped
   internal modes. Steady-state waveform reproduction and startup reproduction
   are separate experiments.
3. Flying-capacitor voltages must not be silently forced in a startup test.
   They may be initialized only in an explicitly named analytical steady-state
   replay, using values derived from the conversion ratio.
4. An ideal switch must not be commanded open with finite inductor current.
   The paper's Mode 4 negative-current target and Mode 5 commutation must be
   represented before the low side is opened.
5. A current comparator that instantaneously changes the same ideal branch
   creates an algebraic chatter loop. A sampled/latched controller may be used
   as a numerical realization only if its sampling/hold behavior is explicitly
   labelled; it cannot invent a new physical threshold.
6. Only one independent change is allowed between recorded experiments.

## Required experiment order

1. `PF-A24-00`: complete 2024 equation/Table-I audit with no SPICE values.
2. `PF-S24-01`: one 2024 four-phase module, analytical periodic-state replay;
   verify topology, phase order, capacitor amp-second balance and inductor
   volt-second balance. No claim about startup or hardware ZVS.
3. `PF-S24-02`: use the recalculated Eq.-(4) result (about 1.4667 nH). Preserve
   the printed Table-I 2.68-nH entry only in the analytical discrepancy audit;
   do not propagate it into subsequent simulations.
4. `PF-S24-03`: four modules at the paper's 48 V/1 V, 1 kW, 5 MHz boundary;
   module timing that is not explicit in 2024 remains a named branch, with
   2025 used only as supporting evidence.
5. `PF-S24-04`: ZVS feasibility envelope using the 2024 1-2% negative-current
   requirement. Missing Coss/snubber/dead-time values remain inputs rather
   than fitted constants.
6. `PF-S24-05`: hardware waveform reproduction only after Mihai supplies or
   confirms the missing device, capacitor and control parameters.
7. Startup, loss, thermal and package layers are separate later gates.

The 2025 experiments are now `AUX-*` evidence. They do not precede or gate the
2024 analytical/topology work and do not provide default component values.
