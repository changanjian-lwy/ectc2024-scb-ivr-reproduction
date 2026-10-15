# A230 - the handover request with a slope lead: start-ups into light load (BOUNDARY)
Method: bridge + cosim (cfg "hand_lead_us"; runs from this commit).
Track A. Written and committed before the runs. Looked at beforehand: the Vo traces of 15 existing start-up records
(A214, A222, A225, A190), evaluated offline with the lead comparator (numbers below).
Decision it changes: whether the start-up's handover request gets a slope lead (closes item 6: N0 into 30 % reaches
1.0510-1.0528 V, limit 1.05 V), and the tested start-up load range on nominal boards (now 50-100 %, though the boards
regulate down to no load since A221).
Cheaper check done first: the 15 records' Vo traces with Vo + tau x slope (slope between consecutive samples, 0.2 us).
At tau 0.7 us the 25 C and cold full-load start-ups (no request fires) reach at most 1.0357 V before 144 us, 9.3 mV
under 1.045 V; the light-load and hot slow ones fire 0.6-1.0 us earlier, at Vo 1.0375-1.0408 V instead of
1.0456-1.0471 V. Budget: 20 runs to 200-300 us, about 1 h at 10 jobs.

## 1. What and why
- Mechanism (A225 record run_u_N0_30.json): in mode S Vo rises at 9.3 mV/us when the 1.045 V request fires (118.8 us);
  mode P enters 0.2 us later and the phase currents turn round about 0.7 us after that, so Vo peaks at 1.0510 V. With
  less load Vo rises faster (8.0-13.9 mV/us in the records; about 25 mV/us expected at no load), so the overshoot past
  the request grows as the load falls.
- Change: the sequencer compares Vo + tau x (Vo's change since the previous sample / the time between them) with
  1.045 V (cfg hand_lead_us = tau; absent = the old comparison bit for bit) - a comparator behind a lead network.
  tau 0.7 us = the request-to-turn-round delay measured above.
- Rows (adopted configuration of A229, one module; load resistance from t = 0, A214's method): N0 into 0 / 10 / 30 %,
  N75 into 0 / 30 %, S75 into 30 % at 25 and 125 C (to 300 us); S75 at 125 C into full load (its request fires, A188),
  N0 and S75 at 25 C into full load (it never fires) (to 200 us). Arms base and lead: 20 runs.
- Sources: Lin, Chen and Chen, IEEE TCAS-II 2019 (DOI 10.1109/TCSII.2018.2886249): open-loop soft start of a
  digitally controlled buck with an initial duty-ratio estimator for a seamless open-to-closed-loop transition (their
  test: Vo within +-5 % after start-up) - the counterpart of A185's loop seed. Maruta et al., IEICE Trans. Commun.
  E100-B(4) 2017 (DOI 10.1587/transcom.2016EBP3197): a digital PID DC-DC in a 380 Vdc system sets its soft-start speed
  from an estimate of the load current. No source uses Vo's slope in the handover comparator; that is our own step.
- Not tested: comparator noise and offset (the slope is taken from noiseless samples), four modules, 0 C / -40 C,
  slow boards below 30 %, a load that changes during the start.

## 2. Criteria
- j1: cosim_regression --quick and --full bit for bit.
- v1 (lead arm, each light row): run completes, Vo <= 1.05 V over the run, peaks <= 200 A, no overlap or shoot-through,
  V_DS <= 40 V, Vo within 1 % over the last 20 us (A225's f6), and Vo >= 0.99 V after mode P's entry.
- v2 (lead arm, S75 125 C full load): v1's terms, handover peak <= base + 2 A, Vo's minimum after the entry >= base's
  - 2 mV and >= 0.99 V.
- v3 (lead arm, N0 and S75 25 C full load): bit for bit the base arm.

## 3. Predictions (not criteria)
- Base arm: N0 30 % 1.050-1.052 V; N0 10 % 1.052-1.058 V; N0 and N75 at no load 1.055-1.065 V; S75 30 % <= 1.0495 V.
- Lead arm: every light row <= 1.047 V; S75 125 C full load handover within 2 A of base; v3 bit for bit.

## 4. Decision rule
- j1 and v1-v3 pass: hand_lead_us 0.7 enters the final configuration; item 6 closes; the tested start-up range becomes
  0-100 % on N0 / N75 and 30-100 % on S75 (25 / 125 C).
- Else: the final configuration stays; item 6 stays open with the base arm's numbers as the start-up range's record.
