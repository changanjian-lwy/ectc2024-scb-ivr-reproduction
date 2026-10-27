# A258 - a ceiling on the limit's count, so it re-arms soon after an overload (BOUNDARY)
Method: cosim. Bridge option ocp "n_cap" (off by default). Track A. Written and committed before the runs.
Looked at beforehand:
- A256 (adopted 2026-10-27): ocp n_susp 6 suspends the limit after 6 limited pulses on any phase. While it is
  suspended, every pulse it would have cut counts +1, and it acts again only when every count is back at 0 (bridge
  ocp_count; nothing caps the count). Under a 125 % overload every pulse would be cut. Replaying A254's arm l records,
  the counts reach 159-201 within 120 us. After the overload ends, the limit would stay off for about as many clean
  pulses, roughly 80-100 us.
- In that window a 1 MHz train is unprotected: A246's N75 train passes 200 A at 21.8 / 32.7 / 40.7 us after its start
  (231.7 A). A256 ran no row where an overload is followed by such a train. Its named limit, "a re-arm under a load
  that is still high was not run", missed this one.
- Commercial up/down counters (TI TPS546D24A) count to a fault threshold and then act. The datasheet survey
  (2026-10-27) gives no saturation detail, so the ceiling here is ours.

Decision it changes: whether the final configuration's count gets a ceiling (n_cap 6).

Cheaper check first: the count replay above (a256_counts.py on A254's records). Budget: 13 runs at 10 jobs, about
1.3 h.

Pre-flight (`python3 a258_analyze.py --preflight`, stand-ins for the new arms):
- t1 passes for A254's run_l_p_N75_1000k / p_S75h_1000k (the limit without an overload: 193.2 / 182.7 A).
- It fails for A246's run_h_ (no limit: 244.6 / 211.1 A). So the row separates a protected train from an
  unprotected one.
- t0 / t2 pass with A256's own records.
- ro_S75h has no stand-in.

Provoking rows:
- the gap itself: pr_N75 / pr_S75h, an overload followed by the 1 MHz train;
- the ceiling's own risk, re-arming more often under a repeated overload: ro_S75h.

## 1. What and why
- n_cap m: a count stops at m, so the limit acts again m clean pulses after any overload ends.
- Arms: s = A256's adopted limit; c = + n_cap 6.
- Rows (2.2 nH boards at 110 A; N0 at 125 A):
  - pr_N75, pr_S75h: A246's p_<board>_1000k (A240's 1 MHz train from 300 us), with +62.5 A from 200 to 290 us before
    it. Arms s and c.
  - ro_S75h: A246's p_S75h_100k with the train's high level at 312.5 A (125 % every 10 us). Arms s and c.
  - REARM, arm c only: A256's rows that re-armed (k_S75h, a_S75h_d2, a_S75h_d20, a_S75_d20).
  - HOLD, arm c only: A256's one-module rows that stay suspended (k_N0, o125_N75, o125_S75h). Their counts never
    return to 0 while the overload lasts, so the ceiling should change nothing.
- Not run: m4_s_p250 (HOLD's argument holds per module); n_cap other than 6; A256's rows that never suspended (count
  <= 2 < 6, equal by construction).

## 2. Criteria
- t-1: tests 726, regression quick + full PASS (tmp/logs/a258_*.log).
- t0: HOLD rows, arm c equal to A256's run_s_ (A246's same).
- t1: pr rows, arm c meets A240's q1 + q2: whole peak <= 200 A, V_DS <= 40 V, Vo above 1.05 V for < 25 us.
- t2: REARM rows, arm c against A256's run_s_:
  - peaks <= + 2 A, NEW <= A256's;
  - |Vo extreme| <= + 2 mV;
  - ladder deviation <= + 0.2 V.
- t3: ro_S75h, arm c against arm s, the same test as t2.

## 3. Predictions (not criteria)
- Arm s on the pr rows misses q1: the limit re-arms 60-100 us after 290 us, and the train peaks as without it (N75
  about 230 A, S75h about 210 A).
- Arm c re-arms within 3 us after 290 us, and the train peaks as A254's (193 / 183 A).
- HOLD equal bit for bit.
- REARM rows re-arm earlier than in A256 (19.5-31.6 us after suspending). Their peaks stay within 2 A, since the
  peaks come before the re-arm.
- ro_S75h, both arms: each high level suspends after about 6 pulses per phase, and the limit re-arms in the low level
  in both arms. The difference between arms is small.

## 4. Decision rule
- **t-1 or t0 fails:** wiring; trace it.
- **t1-t3 pass:** n_cap 6 joins the final configuration. This fixes a gap in A256's adopted mechanism; the user is
  told in the report.
- **t1 fails:** the ceiling is not enough. Measure the re-arm and the train's first peaks, then report.
- **t2 or t3 fails:** name each row's cost. Keep A256's count, write the gap as a stated limit, and leave it to the
  user.
