# A145 - finite switching edges in the cosim plant (BOUNDARY)
Method: mixed (plant change in cosim/plant.py + single-edge harness + RTL cosim of the frozen single-module design)
Track A, package layer. Written and committed before the 22 cosim runs. Seen before writing: the single-edge harness
(a145_edge.py -> a145_edge.json, all rows) and a 200 us timing smoke of e144/e72_l100_n0 and id_q7_l50_n0 (tmp only).
Decision it changes: whether real edges remove A144's overshoot (mechanisms A, B), i.e. whether the loop-inductance
spec is set by voltage or by loss, and what the edges themselves cost. Cheaper check first: the single-edge harness.
Budget: 22 runs x ~30 min at --jobs 10 (3 rounds, ~85 min).

## 1. What and why
- A144: with instantaneous edges V_DS > 40 V at every L (A: own turn-off, steady SH1 16.7 / 27.2 / 34.1 V at
  50 / 100 / 150 pH; B: a hard turn-on of phase k-1 rings SH_k to 24 + 1.7 dV, 47 V start-up, 58.5 V after +4.8 V/1 us).
- Model (plant.py, cfg "edge" {"didt_a_ns", "didt_on_a_ns"}): a switch in an edge is open (the cached off-topology LU)
  and its channel current is a source in the right-hand side. Turn-off with forward channel current i0 = g_on V_DS > 0:
  i0 - didt t down to 0; with i0 <= 0 instantaneous (reverse conduction takes the current, as before). Turn-on with
  V_DS > 0: didt t until V_DS <= 0, then g_on (two Euler steps); V_DS <= 0: instantaneous. Channel energy int V_DS i dt
  recorded per switch and section. Reasons: in saturation a GaN channel is a gate-controlled current source
  (i = g_fs (V_GS - V_th)), so a gate trajectory sets di/dt, not the edge time (the 143 A high side is slower than the
  15 A low side); the source keeps every matrix cached (no K-level conductance keys). Edge steps run in Python
  (KernelSim -> FastSim.step, bit-identical by A95), the C kernel is unchanged; smoke: +27 % / +41 % wall time.
- Rates: 144 / 72 A/ns = 143 A in 1 / 2 ns, the same at turn-on and turn-off (assumed; real values: Mihai).
- Runs: A144's Q 7 cfgs (frozen design = A143 K 4, loop on all four high sides, vds_win 1), L 50 / 100 / 150 pH x
  didt 144 / 72 x rows n0, l_p48_1us, s_p62 (18); e<d>_l0_n0 (no loop: intrinsic edge loss, 2); id_q7_l100_l_p48_1us,
  id_q7_l50_n0 (edges off: identity, 2). Not tested: other modules, L corners, asymmetric on / off rates, 300 pH.

## 2. Criteria (analysis reuses a144_analyze.one(); windows as A144: steady 900-1000 us, step at 1000 us)
1. Identity: edges off = A144 bit for bit (harness rows; id_ runs every field but cfg / wall_s / provenance;
   cosim_regression --full PASS); Fast / Kernel / Kernel2 identical with edges on; h 5 ps vs 10 ps within 0.1 V.
2. Voltage: V_DS <= 40 V over the whole run on all three rows, per (L, didt); L_V(didt) = largest passing L.
3. Controller vs A144's q7 row at the same L (A144's checks): completed, 0 overlaps; late <= q7 + 5; steady turn-on
   V_DS max <= q7 + 1 V; peak (post-step / steady end) <= q7 + 10 A; Vo back within 1 % (n0: vo_end within 1 %);
   new duplicates <= q7's. l0 rows vs b_n0.
4. Loss (n0 steady window): edge power per (L, didt); L-dependent loss P_L = [edge(L) - edge(0)] + damper, damper =
   harness E_loop(L, didt) at 143 A x the run's high-side turn-off rate x (i_off / 143)^2; L_loss = L at 2.5 W (1 %).
5. Cost: edge steps <= 3 % of steps, wall time <= +60 % vs A144.

## 3. Predictions (not criteria)
- Prior I had before the harness, now known wrong: a linear ramp lowers a ring by |sinc(pi t_f / T)|, i.e. -13 % /
  -47 % at 100 pH for 1 / 2 ns. Harness (143 A, Q 7, overshoot above the L = 0 clamp): 100 pH -6 % / -27 %; 50 pH
  -32 % at 144 A/ns but +0 % at 72 (a slow edge reaches the clamp with current still in the channel: inductive turn-off);
  150 pH -2 % / -18 %. The L di/dt during the ramp moves loop energy into the channel instead of removing it.
- Steady SH1 (A144 16.7 / 27.2 / 34.1 V): 144 A/ns 15.5 / 26.3 / 33.7; 72 A/ns 16.7 / 23.3 / 30.3 (+-1.5 V).
  Steady max of all switches (SH2-4, mechanism B at the 3.8 V valley; harness: no edge effect): 29.8 / 28.4 / 34.5 V
  at 144, 29.8 / 28.4 / 31 V at 72.
- Whole run: mechanism B is lowered only where the V_DS fall is long against T_ring (harness rev40: 50 pH 45.7 ->
  43.6 / 34.2 V; 100-150 pH within 1 V). l_p48_1us: 50 pH 54 / 41 V, 100 pH 57 / 54 V, 150 pH 57 / 57 V; n0 / s_p62:
  50 pH 44 / 35 V, 100 pH 46 / 44 V (smoke: 45.5 / 44.4 V in the first 200 us), 150 pH 46 / 46 V.
  -> Criterion 2 fails at every (L, didt); closest 50 pH / 72 A/ns (~41 V).
- Controller holds (criterion 3) everywhere; post-step peaks within +-6 A of q7; turn-off currents -1..-3 A (the
  channel conducts during the ramp, the voltage loop shortens Ton).
- Edge power, n0 steady: no loop 0.8 / 2.5 W; 50 pH 1.4 / 3.9; 100 pH 1.4 / 4.2 (smoke 1.42 / 4.23 at 180-200 us);
  150 pH 1.4 / 4.8 W (144 / 72 A/ns, +-25 %). Almost all in the high-side turn-offs; low sides ~0.
- P_L: 144 A/ns 1.8 / 4.3 / 7.1 W, 72 A/ns 2.1 / 4.1 / 7.2 W at 50 / 100 / 150 pH -> L_loss ~60 pH (A144's
  0.5 L I^2 per turn-off said ~30 pH; the harness damper takes 554 nJ at 100 pH, not 1022 nJ).

## 4. Decision rule
- Some (L, didt) passes 2 and 3: the voltage spec is that pair; loop spec = min(L_V, L_loss).
- None passes 2 (predicted): edges do not remove the hard-turn-on overshoot; it becomes a control requirement (next:
  limit dV at hard turn-ons in start-up / line steps, or check the device's transient rating), and the loop spec is set
  by steady voltage (<= 40 V) and L_loss. The edge rate gets its own loss spec from criterion 4.
- 3 fails somewhere: the frozen controller needs edge compensation (reopens the controller; name the check).
- Either way A144's loss figure is replaced by criterion 4; Mihai: real on / off di/dt with P24's driver, loop Q,
  EPC2067 transient V_DS rating.
