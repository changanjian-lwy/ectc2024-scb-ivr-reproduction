# A228 - adopting the damped loop: the skipping rows' scatter and arm h's remaining rows (BOUNDARY)
Method: cosim (cfg only; RTL and bridge as at 3341c47, A227's code).
Track A. Written and committed before the runs. Looked at beforehand: the t0 records of the three skipping rows
(A224 / A226 / A227, numbers below) and A227's three w records of arm h.
Decision it changes: whether vff rel_gate 25 + kd 355 ns/V (dead band 2), with or without kd_hold, enters the final
configuration - that closes item 9 (re-applications from light load: final configuration 214-248 A, A223; A224
152.5-163.4 A) or leaves it open.
Cheaper check done first: none fits - the question is the cosim's own run-to-run scatter in skipping, which D63 has
no block for. Budget: 36 runs (28 skipping rows to 450 / 750 us, 8 rows to 200-581 us), about 4-5 h at 10 jobs.

## 1. What and why
- A224 (kd 355) and A227 (kd 355 held at the lower Ton limit) passed everything but the skipping rows' valley band,
  judged on one run per arm, and A227's h2 was two-sided. The t0 records (true valleys, last 20 us; no load 60 us):
  N0 10 % d0 -16.2..-13.6, k -16.8..-11.6, h -16.8..-12.2 A; N75 10 % k -18.0..-12.1, h -18.5..-11.2 A; N0 no load
  d0 -22.8, k -23.1, h -23.1 A (upper end -15.6 A in all three). Changes of about 1 A at the band's edge cannot be told
  from the scatter of one run.
- Part S measures that scatter: the three skipping rows with the load released at 300.0 (t0), 301.3, 302.7 and
  304.1 us (t1-t3; about 3, 6.5 and 10 periods of 0.41 us later - A174 / A206 sample step positions the same way)
  in three arms: d0 = the final configuration as it is, k = gate + kd 355 (A224), h = k + kd_hold 1 (A227).
  New runs: t1-t3 x 3 rows x 3 arms + N75 10 % d0 at t0 = 28.
- Part R runs arm h on A224's other rows (w20_N0, w30_S75h, u_N0, k_N0, l_N0_p48, l_N0_m80, k_S75h, h_S75_25): A224
  scored arm k on them, arm h has only w0_N0, w5_N0 and w5_N75 (A227). 8 runs.
- Not tested: other loads, temperatures and boards for the skipping rows; more kd values (A224's margin to the
  handover's edge on S75 at 125 C stays 1.24-1.5x); four modules.

## 2. Criteria
- q1 (part S, per row and arm k / h): no more runs fail than d0's at the same row, where a run fails unless it
  completes with A216's s1 and s2, no late fire at the end, true valleys found, and on the 10 % rows z1r (A220).
- q2 (part S, per row and arm k / h, one-sided against d0): mean over the four instants of each run's lowest true
  valley >= d0's mean - 1.0 A, and mean of each run's highest true valley <= d0's mean + 1.0 A.
- q3 (part R and A227's w records, arm h): A224's e1 (w rows), e2 (u_N0, k_N0), e3 (line rows) and e4 (every row),
  against the same references A224 used (A223's g25 records; A222's S75 25 C start-up).
- The band -20..-12 A is not a criterion here: d0 itself sits 2.8 A below it at no load (A226). Each arm's count of
  runs inside the band is reported.

## 3. Predictions (not criteria)
- d0's per-run lowest and highest true valleys spread over about 1 A across the four instants.
- Arm h passes q2 on all three rows (means within 0.7 A of d0's). Arm k misses q2 on N0 10 %'s upper end (mean 1.2-2
  A above d0's): its derivative term acts while skipping (A224: Ton off its 4.0 ns limit up to 4.91 ns).
- Part R: arm h is bit for bit arm k on k_N0, l_N0_p48, l_N0_m80, k_S75h and h_S75_25 (the PI output never reaches
  its lower limit at full load or at the handover); it differs on u_N0, w20_N0 and w30_S75h, within 3 A of arm k.

## 4. Decision rule
- Arm h passes q1-q3: the final configuration becomes V7 + A222's trims + vff rel_gate 25 + kd 355 ns/V, dead band 2,
  kd_hold 1; item 9 closes with the re-application numbers of arm h; the docs follow.
- Else arm k passes q1 and q2 (its other rows passed A224's e1-e4): the same without kd_hold.
- Else: the final configuration stays as it is; item 9 stays open with A224's numbers; the scatter is reported.
- Both pass: arm h, because it keeps the derivative term out of the skipping regime, where A224 saw it act.
