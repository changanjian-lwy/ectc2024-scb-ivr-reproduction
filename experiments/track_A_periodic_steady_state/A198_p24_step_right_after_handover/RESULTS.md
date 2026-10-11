# A198 - the worst row right after the handover (RESULTS)
Boundary: 8744c8f. Records: release records-a198 (15 runs, logs). Analysis: a198_analyze.py -> a198_summary.json.
Plant V5, one module, final configuration (A188 start-up, lead 9.5 ns on S75 and 8 ns on N0, t_il 1.0 ns).
+4.8 V / 1 us at 2 / 10 / 20 / 40 / 80 us after mode P's entry. cosim_sources_modified False; 10 runs started at
8744c8f and 5 at 2e46b6f (git diff on src/ is empty).

## 0. Verdict
- **The row is not covered in the first 40 us after the handover: 4 of 15 runs exceed 200 A (c2).**
  - S75 at 125 C: 202.8 / 214.4 / 217.3 A with the step 2 / 10 / 20 us after the entry.
  - S75 at 25 C: 206.1 A with the step 20 us after the entry (195.5 / 197.6 A at 2 / 10 us).
  - N0 at 25 C passes at every instant; its largest value, 193.7 A, is at 2 us.
- **From 40 us on all three boards pass at both tested instants:** S75 at 125 C 186.7 / 187.2 A, S75 at 25 C
  195.3 / 192.4 A, N0 179.9 / 178.5 A.
- **By the decision rule the specification states a hold-off of 40 us after the handover for this row.** Before it
  the largest tested value is 217.3 A (S75, 125 C, step 20 us after the entry). No remedy is run under this number.
- c1, c3, c4 and c5 pass on all 15: COMPLETED, 0 shoot-throughs, V_DS <= 33.6 V, Vo within 18.1 mV of 1 V, back
  inside 1 % within 31.2 us.
- **Where the excess comes from** (read from the records, phase by phase):
  - Every largest peak is on phase 1. Its rail (Vin minus the first series capacitor) takes the step: 12.3-12.6 V
    before, 16.2-17.0 V two microseconds later. That is the known line-step mechanism (A108).
  - At 125 C the handover has its own phase-1 peak, 184.5 A about 19 us after the entry, while the loop's on-time
    is raised. All three early steps peak 16-22 us after the entry: the rail's jump lands on that raised on-time.
    At 40 us the handover's peak has passed and the step gives 186.7 A.
  - At 25 C with the step at 20 us the peak comes 7.3 us after the step. Phase 1's valley is then +28.6 A (it turns
    on without a reversed current) and phases 2-4 reach -67..-86 A. With the step at 80 us phase 1's valley stays at
    +3.2 A. Why the valley is lost at 20 us and not at 2 or 10 us is not traced; 20 us is where the lead's ramp ends.
- The settled row is not the worst instant. S75 at 125 C gives 186.7-187.2 A at 40-80 us against 194.6-196.3 A at
  500 us (A197).

## 1. Criteria (c2 = whole-run peak; the peak after the step is the whole-run peak in every run)
| board | handover alone | step 2 us after entry | 10 us | 20 us | 40 us | 80 us | settled, 500 us |
|---|---|---|---|---|---|---|---|
| N0, 25 C | 165.4 A | 193.7 | 183.5 | 179.0 | 179.9 | 178.5 | 182.8 (A185) |
| S75, 25 C | 154.0 A | 195.5 | 197.6 | **206.1** | 195.3 | 192.4 | 195.8-197.1 (A192) |
| S75, 125 C | 184.5 A | **202.8** | **214.4** | **217.3** | 186.7 | 187.2 | 194.6-196.3 (A197) |
- Peak instant after the step (us): N0 0.9-2.0; S75 25 C 17.1 / 8.0 / 7.3 / 20.4 / 19.7; S75 125 C 16.4 / 6.4 / 1.9 /
  16.4 / 22.7.
- Vo after the step: N0 -8.6..+18.1 mV; S75 25 C -14.2..+12.9 mV; S75 125 C -11.8..+14.3 mV. Back inside 1 %: N0
  31.2 us at 2 us, otherwise <= 5.7 us; S75 <= 30.7 us.
- Diagnostic layer: N0 has no late fire and no NEW event. S75 has 2-131 late fires after the step (most with the
  step at 2 us) and 12-44 NEW events.

## 2. Predictions
- Held: c1 and c3 everywhere; N0 passes (178.5-193.7 A); a miss on S75 at 25 C at one of the first three instants;
  misses on S75 at 125 C at 2 to 4 instants (3); c4 passes.
- Missed: the largest 125 C value is at 20 us, not near 2 us, and it is 217.3 A (predicted at most 215 A); S75 at
  25 C reaches 206.1 A (predicted at most 205 A); at 80 us the boards are 3.4-9.1 A below their settled values, not
  within 3 A; c5 does not miss.

## 3. Limits
- Five instants. The boundary lies between 20 and 40 us and is not resolved further. Between 80 us and 356 us the
  row itself is not run (A194's draws there are milder events).
- Three board and temperature points, one row. S80, S0, cold boards, falling steps, load steps and four modules in
  this window are not run.
- The entry instant differs between boards (131.4 us on hot slow boards, 144.0 us otherwise), so the hold-off is
  counted from mode P's entry, not from enable.
