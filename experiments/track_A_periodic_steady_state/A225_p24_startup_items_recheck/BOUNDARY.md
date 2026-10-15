# A225 - controller items 2, 5 and 6 on the candidate configuration of A223 / A224 / A227 (BOUNDARY)
Method: cosim, cfg only (on A227's code: kd_hold). Track A. Written after A224's results, committed before A225's runs, which
go with A227's (A227 decides whether the candidate is adopted; A225's rows do not skip, so kd_hold does not reach
them except where the PI output touches the lower limit, as after a light-load handover).
Decision it changes: whether the specification keeps its 40 us hold-off after the handover (item 2), its 50 %
lower bound on the start-up load (item 6) and its slow-board two-cycle orbit (item 5), or whether the start-up and
handover are redesigned for them (A228 on).
Cheaper check done first: existing records. Item 5 (a195_analyze.alt, mean |valley change| per period over 40 us,
S75): plant V6 at 25 C 3.7-7.8 A (A206 lat 0, A215 lat 16 / 32, A211 at 40-100 %), at 125 C 0.6-3.5 A; the same
125 C row on V7 (A221 run_k_B_S75_hot_p5_ls0p3.json) 0.03 A, and A223 / A224's final rows 0.03 A at 125 C, 0.5-0.6 A
at 25 C within 60 us of the handover (A222 run_s_S75_25_r2.json). V7's core resistor is the change between them.
Items 2 and 6 have no V7 record: A223 / A224 changed the handover (kd 355 moved S75 125 C's handover peak from
+22 us, 180.0 A, to +2.2 us, 178.9 A, and raised Ton there by about 3 ns).
Budget: 14 runs of 200-500 us, about 1 h at 10 jobs.

## 1. What and why
- Candidate configuration: plant V7, A222's trims, ton_lat 16, ton_min 4 ns, vff rel_gate 25 (A223), kd 355 ns/V with
  a 2-code dead band (A224) held at the lower Ton limit (A227), skipping with res_ofs_a = zcd_a = 8 ns x Vo / L; one
  module. If A227 does not adopt it, these results are stated for the candidate, not the final configuration.
- Item 2 (A198, V5): +4.8 V / 1 us 2 / 10 / 20 us after mode P's entry reached 202.8 / 214.4 / 217.3 A on S75 at
  125 C and 195.5 / 197.6 / 206.1 A at 25 C; N0 193.7 A at 2 us. a rows: the same seven on the candidate.
- Item 6 (A214, V6): the start-up into 30 % of the load reached 1.0528 V on N0 (limit 1.05 V); slow boards at 30 %
  were not run. u rows: N0, S75 25 C, S75 125 C at 30 % (the slow boards' minimum load, A210).
- Item 5 (A195, V2 / V5): s rows: S75 25 C at 100 and 50 % to 500 us, and both with twice r_core (rc2), because the
  orbit's absence would rest on the core's damping, whose value at 20-25 MHz is an extrapolation (A221).
- Not tested: 0 / -40 C, four modules, other L, other step instants than A198's.

## 2. Criteria (each item on its own)
- f2 (a rows): whole-run peak <= 200 A, no overlap or shoot-through, V_DS <= 40 V, Vo within 1 % over the last 20 us.
- f6 (u rows): Vo <= 1.05 V over the run, peaks <= 200 A, no overlap or shoot-through, V_DS <= 40 V, Vo within 1 %
  over the last 20 us.
- f5 (s rows): every phase's mean |valley change| from one period to the next <= 1 A over the last 40 us (A195:
  nominal boards <= 0.9 A).

## 3. Predictions (not criteria)
- a rows: S75 125 C at 10 / 20 us 195-215 A (the rail's jump still meets a raised Ton; kd raises Ton after the
  handover by about 3 ns), at 2 us within 5 A of A198; S75 25 C within 5 A of A198; N0 <= 195 A. Item 2 not closed.
- u rows: N0 1.049-1.053 V (V7's core lowers mode S's Vo by ~0.5 mV, kd pulls Ton down while Vo still rises);
  slow boards' entry earlier than at 50 % (A214: 114 / 109 us), Vo <= 1.05 V.
- s rows: <= 1 A at 100 % and 50 % (V7), rc2 <= 1 A at 100 %, 1-3 A at 50 %.

## 4. Decision rule
- f2 on all seven: the hold-off is dropped for the instants run; else item 2 gets a redesign of the window after
  the handover (A228), with these records as its start.
- f6 on all three: the tested start-up range extends to 30 %; else item 6 gets a load-aware loop seed (A228 on).
- f5 on all four: item 5 is recorded as a V2-V6 plant artefact (no core damping), closed on V7; if rc2 misses, the
  claim is stated with the damping it needs.
