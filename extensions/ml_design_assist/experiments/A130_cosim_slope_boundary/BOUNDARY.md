# A130 - Line-slope boundary of the adopted vff + gth 100 design (BOUNDARY)
Extension ml_design_assist. Written and committed before the cosim runs. Looked at beforehand: A129 results/scripts only; D63 predictions below were computed, no cosim run.
Decision it changes: the bus-slew spec (V/us limit per step amplitude) of the 2.5 MHz design. Today only known: <= 4.8 V at >= 1 us (falls tested 1/2/3/5 us, rises 1/5 us), 8 V fall >= 10 us.
Cheaper check done first: D63 with the gated RTL law (a130_predictions.json). Budget: 10 cosim runs, ~5 min at --jobs 6 (EEK5101 VM is up).

## 1. What and why
- Rows (cfg = A129 cfg_g125_l_m48_5us, only line_step changed): -8 V/6 us, -8 V/7.5 us, +4.8 V/2 us, +4.8 V/3 us, +8 V/10 us.
- Each row at two step phases (t_us 800 and 800.33) because moving the step by < 1 period moves the post-step peak 2-7 A (A129 post hoc).
- Spec = fastest passing slew at each step amplitude, combining these rows with A129's (4.8 V: fall 1/2/3/5, rise 1/5 us; 8 V fall 5 [208 A, fail] and 10 us [170.9 A]).
- Not tested: other amplitudes, load steps, 8 V rise below 10 us.

## 2. Criteria
1. Row passes if both phases give peak after step (max highoffs i_a, t >= 800 us) <= 200 A; "marginal" if the worse phase is within 7 A of 200 A (193-200 A).
2. No late fires > 100, no runaway (peak > 400 A) in any run.
3. Spec per amplitude = fastest passing slew, with the neighbouring slower tested slew also passing (no non-monotone hole); a hole is reported, spec then taken above the hole.

## 3. Predictions (not criteria)
D63 gated peak: -8 V/6 us 178.2 A, -8 V/7.5 us 171.3 A, +4.8 V/2 us 180.8 A, +4.8 V/3 us 180.0 A, +8 V/10 us 196.1 A (gate never opens in these; without ff 204.5 / 197.6 / 218.4 for the rises).
A125 bands (80%): M 155-201, 149-193, 158-203, 157-203, 171-221; G 176-211, 169-203, 178-214, 178-213, 193-232.
Expectation: D63 underestimates -8 V falls (-10% at -8 V/5 us), so -8 V rows likely above D63; -8 V/6 us may fail.

## 4. Decision rule
Pass/marginal table -> spec in V/us per amplitude into the scorecard T18 row and scb-map. A row above 200 A is a stated limit, not a reason to add a control rule in this experiment.
