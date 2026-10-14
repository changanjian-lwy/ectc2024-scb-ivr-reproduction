# A223 - phase 1's relative cap only while Vin rises (BOUNDARY)
Method: RTL (scb_vff input rgth, scb_ctrl cfg_vff_rgth, bridge cfg vff "rel_gate"; off = bit-identical) + cosim; D63
as the cheaper check. Track A, controller item 9. Written and committed before the runs, with the code.
Decision it changes: whether the final configuration limits phase 1's relative cap to rising Vin (closing item 9), and
whether the specification can state load re-applications from light load to full load.
Cheaper check done first: a223_predict.py (D63, RTL integer arithmetic of scb_vff) -> a223_predictions.json.
Budget: 20 runs (10 pairs), about 3 h at 10 jobs.

## 1. What and why
- Problem 9 (A216, plant V6, records `A216_p24_skipped_rounds/cosim/run_w_N0_25_20_up_ns.json`, `run_w_N0_25_5_up.json`):
  +200 A from 20 % reaches 249.8 A, +237.5 A from 5 % 235.4 A. In the first record phase 1's on-time after the step
  is 13.7 / 15.8 / 19.3 / 23.9 ns in the 2-4 us bins from 380 us while phases 2-4 are at 22 / 24 / 33 / 37 ns; rail 1
  rises 11.3 -> 16.3 V, phases 2-4 turn on at +83..+130 A (phase 1's short on-time sets the period), phase 4 peaks
  at 243 A at 384-388 us.
- Cause: scb_vff's relative cap (A135 / A136, adopted) is 1.25 x tlp x rss / rail, tlp ton's low-pass over 64 samples.
  It exists for rising Vin (rail 1 jumps before the ladder follows; A134-A136). At constant Vin rss = rail, so it
  is 1.25 x tlp, and any step that raises the loop's Ton faster than tlp follows holds phase 1 alone.
- D63 (L0, final Ton limits): the cap binds after every re-application from 5-50 % (55-163 periods), also on a
  specified +62.5 A from 30 % (57 periods); without it the peaks fall 169 -> 146 A (+200 A from 20 %) and 197 -> 145 A
  (+237.5 A from 5 %). The same cap on all four phases is worse (278 / 361 A, Vo +117 / +180 mV): not run.
- Change: with rgth != 0 the cap acts only at samples where rail - rss (= Vin's one-step prediction above lp20) is
  >= rgth codes; elsewhere no cap and tlp restarts from ton. rgth 25 codes = 0.5 V. In D63 the adopted cap binds
  in periods 2-79 after the start of +4.8 V / 1, 5, 20 us and +8 V / 10 us; rail - rss stays >= 25 codes over periods
  0-1 .. 3 to 144-185, so the gate covers every binding period (at +4.8 V / 50 us the cap does not bind). A single
  threshold, no hysteresis: after a rise lp20 stalls up to 63/256 code below Vin (Q8 shift), so "until 0" would not
  close. With an ideal Vin source (the cosim) rail - rss is 0 in steady state; a real bus's ripple must stay below
  0.5 V (stated as a requirement, not tested). No published source for this gate; it follows A129's falling-term
  gate (gth) in form.
- Rows (one module, final configuration on plant V7 = A222's trims, ton_lat 16, ton_min 4 ns; skipping on the
  light-load rows; arms off and g25): w0_N0, w5_N0, w20_N0 (N0 released at 300 us to 0 / 5 / 20 %, back to full
  load at 380 us), w5_N75 (N75 to 5 %), w30_S75h (S75 125 C to 30 %, +175 A), u_N0 (N0 to 5 %, +62.5 A), k_N0
  (A222's k row), l_N0_p48 / l_N0_m80 (+4.8 V / 2 us, -8 V / 10 us at 500 us), k_S75h (S75 125 C +4.8 V / 1 us,
  the tightest row).
- Not tested: four modules (the gate is per module), other step positions and temperatures, a Vin with ripple, a
  load step during a rising Vin (the cap holds phase 1 there as before).

## 2. Criteria
- j1: unit tests 106 of 106 (two new: no cap at constant Vin - fails without the gate; A136's cap on a rising Vin);
  cosim_regression --quick and --full bit for bit; k_N0_off equals A222's run_k_n_s_p62.json bit for bit.
- c1 (item 9): on every w row the g25 arm's whole-run peak <= 200 A, no overlap, V_DS <= 40 V, Vo within 1 % over
  the last 20 us.
- c2 (load rows within the specification, u_N0 and k_N0): g25's post-step peak <= off's + 1 A, Vo's post-step extreme
  no more than 1 mV further from 1 V than off's.
- c3 (line rows, l_N0_p48, l_N0_m80, k_S75h): g25's post-step peak within 1 A of off's, Vo's extreme within 1 mV.
- c4 (before the step): each pair's sections before the first re-application (w, u rows: 380 us) or the step (k, l
  rows: 500 us) bit for bit; where they differ, peaks within 1 A and Vo within the off arm's range +- 1 mV.

## 3. Predictions (not criteria)
- Off arm on V7: w rows 220-260 A (V6 249.8 / 235.4 A), phase 1 held as in A216.
- g25 arm: w rows 160-200 A; phase 1's on-time within 1 ns of phases 2-4 from the second period after the step;
  rail 1 <= 13 V. D63 ranks (146 / 145 A) but under-predicted the off arm by 80 A.
- u_N0 / k_N0: g25 the same within 0.5 A (D63: the cap binds after +62.5 A from 5-30 %, peak -3 A).
- Line rows: within 0.5 A, l_N0_m80 bit for bit (the gate is shut on a falling Vin; D63: the cap never binds there).
- c4: bit for bit (at the handover phase 1's on-time equals the others', 41 ns against a cap of 55.6 ns, A222's
  records; without the divider the ton registers load once per sample instead of twice, with the same values).

## 4. Decision rule
- j1 and c1-c4 pass: vff rel_gate 25 joins the final configuration; item 9 is closed for these rows, and the
  specification states re-applications from light load to full load on the boards run.
- c1 misses but c2-c4 pass and every w row's peak falls: adopted (it removes a found defect without harm); the
  remaining mechanism is traced in the records and item 9 stays open with the new numbers.
- c2, c3 or c4 misses: not adopted; the records show where the cap's absence or the gate's timing matters.
