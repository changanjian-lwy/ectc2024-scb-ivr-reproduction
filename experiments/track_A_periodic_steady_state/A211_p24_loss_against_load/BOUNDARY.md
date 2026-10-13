# A211 - the loss books against the load on the binding boards, and what shedding modules would save (BOUNDARY)
Method: cosim with the frozen RTL (cfg only) on plant V6; a composition for four modules. No code change.
Track A, main line. Written and committed before the runs. Looked at beforehand: A210's nine rows (2026-10-14, not
yet written up): with ton_min_ns 4.0 ns the slow 0.75 L0 board regulates at 30 and 20 % but books 15-19 W of
semiconductor loss there (75-83 %), 9-12 W of it in high-side edges at 5.5-6.6 MHz; N75 books 6.5 W at 30 %; N0
4.2 W (A208). The frequency rises as the load falls (period about 12 on-times), and slow edges cost more each.
Decision it changes: whether shedding whole modules (LSCB's phase shedding; it needs RTL) is worth building: at which
system load fewer modules at a higher share lose less than all four at a low share on the binding boards. And the
efficiency-against-load line of the specification.
Cheaper check done first: none; the full-load books of these boards on V6 do not exist (A206 ran them with steps).
Budget: 9 runs of 450 us, the S75 rows about 100 min, at 9 jobs.

## 1. What and why
- Rows (A210's cfgs: A206's board cfg, ton_min_ns 4.0 ns, release at 300 us, end 450 us, books over the last
  10 us): S75 at 25 C with 100, 75, 60, 50, 40 % of 250 A; N75 at 25 C with 100, 75, 60, 50 %. With A210's rows
  (S75 30, 20 %; N75 40, 30 %) and N0's (A206, A207, A208: 100 to 20 %) this gives three loss curves.
- Composition (a211_analyze): four equal modules of one board class, equal sharing, an idle module at 0 W. For each
  system load: the loss with all four on, and with the number of modules on that loses least, each running module
  inside its board's tested range. Not a run: the frozen controller cannot shed a module.
- Not tested: 0 and 125 C on these rows, fast devices, four modules in cosim, the loss outside the switches (gate
  drive grows with the frequency and is not in the books; inductors, capacitors).

## 2. Criteria
 Every row works: r1, r2, r4 as in A210 (the board's valley band, no late fire in the last 20 us).
The result is the loss curve; there is no pass mark on the loss.

## 3. Predictions (not criteria)
- Every row works. Registers far above 4.0 ns.
- S75: 24-30 W at 100 % (N0: 20.15 W), 17-21 W at 75 %, 15-19 W from 60 to 40 %: the high-side edges stay near
  9-11 W while conduction falls. Efficiency 90-91.5 % at 100 %, under 90 % from 60 % down.
- N75: 21-24 W at 100 %, 13-15 W at 75 %, 9.5-11.5 W at 60 %, 8-9.5 W at 50 %.
- Composition, S75: from 50 % of the system load down, fewer modules on lose at least 20 % less than all four.
  N0: shedding saves under 10 % anywhere above 20 %.

## 4. Decision rule
- The three curves go into the coverage file as the efficiency-against-load line, each with its board.
- If on a board class fewer modules save 20 % or more of the semiconductor loss at some system load of 50 % or
  less, shedding is named as worth building, with the load where it starts to pay; otherwise it is named as not
  worth its RTL on efficiency grounds. Building it is the user's decision.
