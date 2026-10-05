# A144 - commutation-loop inductance in the cosim plant (RESULTS)
Boundary: bdca9a2. Records: release records-a144 (17 runs, 144 MB). Summary: a144_summary.json (a144_analyze.py);
single-edge check: a144_edge.json. All runs from committed code (cosim_sources_modified False).

## 0. Verdict
- **Plant:** loop inductance in (cfg "loop"); off = bit-identical (3/3 rows vs A143, cosim_regression --full PASS).
  h 10 ps is enough: the loop rings with the switch Coss at 140-550 MHz (~200 steps per period), not 16 GHz.
- **Controller survives the ring at Q 7:** 50-300 pH, three rows: 0 late fires, 0 new duplicates, steady turn-on
  V_DS +0.86 V at most, post-step peaks -6..+3 A against the loop-free run. No ring blanking needed. L_C = 300 pH.
- **Device voltage fails at every L (whole run <= 40 V):** max 58.5 / 57.8 / 57.1 / 74.4 V at 50 / 100 / 150 / 300 pH.
  Two mechanisms:
  - (A) own turn-off, D65's: steady SH1 16.7 / 27.2 / 34.1 / 52.0 V; it dominates from ~150 pH.
  - (B) new: a hard turn-on of phase k-1 steps SH_k's upstream node by its V_DS (dV), and SH_k (already blocking
    2 rails, 24 V) rings to ~24 + 1.7 dV, independent of L. Start-up (mode S, dV 14.8 V): 46-47 V; +4.8 V / 1 us
    line step (dV 19.1 V): 57-58.5 V; both at 50-150 pH. In steady state (dV 3.8 V) SH2-4 sit at 28-30 V.
  - Steady state alone stays <= 40 V up to 150 pH (35.0 V).
- **Damping decides the controller verdict:** undamped (150 / 300 pH, l_p48_1us) the ring never decays, the valley
  tracker locks onto it (turn-on V_DS mean 8.5-9.8 V, max 35-36 V), 8000+ late fires, 18 / 97 new duplicates,
  225 / 214 A, V_DS 87 / 110 V.
- **Loss (not in D65):** 0.5 L i_loop^2 per turn-off = 3.9 / 7.7 / 11.3 / 24.5 W at 50 / 100 / 150 / 300 pH
  (1.6 / 3.1 / 4.5 / 9.8 % of 250 W); a 1 % budget means <= ~30 pH, tighter than the steady-state voltage.
- D65's energy bound matches the plant's single edge within -1.0..+1.5 V; the series-LC balance
  int (v - V_rail) C dv overestimates by 10-12 V (it ignores the low-side Coss taking part of the current).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | b_ runs = A143 records; regression | PASS (every field; full regression PASS) |
| 2 | V_DS <= 40 V whole run, Q 7 | FAIL at all L (above); L_V none |
| 3 | controller vs b_, Q 7 | PASS at all L: late 0 / new 0; on-V 4.80 / 4.26 / 4.22 / 3.79 vs 3.94 V; post peaks 178.5 / 178.2 / 183.6 / 174.8 vs 180.6 A (l_p48_1us), 178.7 / 177.4 / 176.2 / 176.0 vs 177.7 A (s_p62); Vo back within 1 % |
| 4 | damping flips a verdict? | yes: criterion 3 fails undamped |

Predictions: SH1 steady 18 / 29 / 36 / 53 V -> 16.7 / 27.2 / 34.1 / 52.0 (held); SH1 after the steps 25 / 38 / 47 / 68 ->
25.0 / 36.6 / 50.7 / 73.5 (+3..5 V at 150-300 pH: 13.2 V rail, turn-on ring adds to the turn-off current); SH2-4 within
3 V of SH1 -> wrong (mechanism B); L_V 100 pH -> wrong (none); controller -> held; loss 8.2 W per 100 pH -> 7.7 W.
Side effect: the +4.8 V line step's Vo excursion turns from -11.8 mV (7.6 us outside 1 %) to +7.6..+8.3 mV (never outside).

## 2. Decision (registered rule) and limits
- No L passes at 50 pH -> the instantaneous switching is too pessimistic; next parasitic: finite switching speed
  (turn-on and turn-off; mechanism B is an ideal-step excitation, a 1-2 ns edge against a 2-3 ns ring lowers it).
  Loop damping Q joins the D65 question list for Mihai. For the spec: loss sets ~30 pH (1 %), steady voltage 150 pH;
  hard turn-ons (start-up, fast line steps) bind SH2-4.
- Limits: Q 7 parallel damping is assumed (undamped is a bound, not a circuit); switching is instantaneous; the loop
  is lumped upstream of each high-side drain and the die V_DS is sensed; one module, L x 1.0, three rows.
