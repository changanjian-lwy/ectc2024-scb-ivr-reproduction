# A144 - commutation-loop inductance in the cosim plant (BOUNDARY)
Method: mixed (plant: circuit-model change in cosim/circuit.py; RTL cosim of the frozen controller, RTL unchanged)
Package layer, track A. Written and committed before the cosim runs. Looked at beforehand: a144_edge.py (single-edge
plant check, a144_edge.json), a 30 us smoke test (timing only), the A143 records of the three rows (baseline values).
Decision it changes: the commutation-loop inductance spec given to Mihai (voltage and loss), and whether the V_DS
comparators (czh / czl, valley cva) need ring blanking.  Cheaper check done first: D65 (analytic) + the single-edge
plant check below.  Budget: 17 runs x 7-50 min, --jobs 6 (EEK5101 VM up), ~1.5 h wall.

## 1. What and why
- D65 put the loop limit for a 40 V device at 141 pH (143 A) / 72 pH (200 A) from an energy bound; the plant had no
  loop inductance, so neither the closed-loop peaks nor the effect of ringing on the V_DS comparators were known.
- Plant change (cfg "loop" {"l_ph", "rp_ohm", "phases"}): l_ph in series with every high-side switch, upstream of its
  drain (new node h_k; the switch's Coss now between h_k and its source; its V_DS is the die's). rp_ohm across the
  inductance as damping. Off (no "loop") = no new state, every matrix as before. Also cfg "vds_win" 1: each section
  records the 8 switches' peak V_DS since the previous one (records only).
- Damping is an ASSUMPTION: Q 7 (rp = 7 sqrt(L / (2 Coss(12 V))) = 0.82 / 1.16 / 1.43 / 2.02 Ohm at 50 / 100 / 150 /
  300 pH; parallel so that it costs no DC loss). Undamped runs bracket it. Turn-off is instantaneous (worst case;
  gate-drive speed is the next parasitic).
- Single-edge check (done, a144_edge.json): SH1 off at 143 / 200 A, 48 V: plant peak (undamped) within -1.0..+1.5 V of
  D65 at 25-300 pH (100 pH 143 A: 32.4 vs 33.3 V); the series-LC formula 0.5 L I^2 = n int (v - V_rail) C dv gives
  10-12 V more and is only reached with no low-side Coss (n_low 1 / 3 / 6: 36.1 / 32.4 / 35.3 V at 100 pH). h 10 ps
  converged (vs 2.5 ps < 0.02 V); Reference / Fast / Kernel plants bit-identical with the loop on.
- Rows: frozen single-module design (A143 K 4 cfgs = A141 F + lo_learn 4), L x 1.0, n0 / l_p48_1us (+4.8 V over 1 us
  at 1000 us) / s_p62 (+62.5 A at 1000 us). Runs: b_<row> loop off; q7_l{50,100,150,300}_<row>; u_l{150,300}_l_p48_1us
  undamped. Not tested: low-side loop, Cs ESL, finite switching speed, four modules, L corners.

## 2. Criteria
1. Identity: b_<row> equals the A143 record of its row in every field except the added "vds_win_v" (sections,
   *_last lists, steps, ipk_a, late_fires, vds_max_v); scripts/cosim_regression.py --full PASS (done: PASS).
2. Device voltage at L (Q 7): every switch's peak V_DS over the whole run <= 40 V (EPC2067 rating) on all three rows.
   L_V = the largest L in {50, 100, 150, 300} that passes.
3. Controller at L (Q 7), each row against its b_ run: (a) COMPLETED, 0 overlaps; (b) late fires <= b + 5; (c) steady
   window 900-1000 us: high-side turn-on V_DS max <= b + 1.0 V (b 3.94 V); (d) post-step peak phase current
   <= b + 10 A and Vo back within 1 % (back_within_1pct_us finite); (e) no NEW / FF duplicate events (A142 oracles).
   L_C = the largest L where all hold on all three rows.
4. Damping: u_ vs q7_ at 150 / 300 pH on l_p48_1us - does the verdict of 2 or 3 change? (reported, decides whether Q
   is a question for Mihai).

## 3. Predictions (not criteria)
- SH1 peak V_DS from the edge check (Q 7, 143 A steady / ~180 A after the steps): 50 pH 18 / 25 V, 100 pH 29 / 38 V,
  150 pH 36 / 47 V, 300 pH 53 / 68 V -> L_V = 100 pH (post-step rows decide). SH2-4 within +-3 V of SH1 (same rail
  and turn-off current); undamped +4..+9 V.
- Controller: passes at 50-100 pH; at 300 pH the valley tracking may catch the ring (turn-on V_DS up) - uncertain.
- Loss (analytic, from highoffs i_loop_a): 0.5 L I_off^2 x 4 phases x 1.98 MHz = 8.2 W per 100 pH at 144 A
  (3.3 % of 250 W), dissipated in the damping / ring.

## 4. Decision rule
- Spec for Mihai: L_spec = min(L_V, L_C), with its loss at 144 A. If none passes at 50 pH: the instantaneous turn-off
  is too pessimistic for the 230-320 pH literature loops -> next parasitic is the gate-drive turn-off speed.
- 2 passes where 3 fails -> comparator ring blanking is the next (RTL) experiment. 3 passes up to 300 pH -> the
  comparators are robust and voltage / loss alone set the spec.
- 4 flips a verdict -> Q (loop damping) goes on the D65 question list for Mihai.
