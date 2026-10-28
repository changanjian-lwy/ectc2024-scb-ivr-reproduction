# D89 - overload rating and a train that starts while the limit is suspended

Script: `scripts/p24_overload_rating.py` -> `diagnostics/D89_overload_rating.{json,png}`. No co-simulation. Written
2026-10-28, after A258, for two items that item 10 lists as not run: overloads above 125 %, and a train less than
10 us after an overload ends. Both are read off existing records of the final configuration (plant V7, one module,
25 C except S75h, whose slow devices run at 125 C; A244 cfg_w + rev_n 16 + hold_floor_ns 3.0 + ocp {110 / 125 / 140 A, t_ns 1.0, n_susp 6, n_cap 6}).

## 0. Result

- **Overload rating: about 136 % (341 A per module).** Once the limit suspends, the loop carries the overload, and
  the steady peak follows the load at 0.539-0.544 A per ampere on all four boards. Extrapolated from the 125 % rows,
  the peak reaches the 200 A budget at 138.9 / 138.1 / 136.4 / 139.5 % (N0 / N75 / S75h / N13). Above that, a
  suspended limit lets the peak through, and a total over-current trip would be needed. None is modelled (A256 cites
  TPS54A20's hiccup with a re-pre-charged Ct).
- **A train that starts while the limit is suspended re-arms it about 2.2 us in.** Of the unprotected trains' pulses,
  only 3-7 % last the 11 ns from the 110 A crossing to a cut. The train's own clean pulses therefore run the count
  down from the ceiling about as fast as base load does: 2.21 / 2.17 us (N75 / S75h). Unprotected 1 MHz trains first
  passed 200 A 3.9 us (A246 N75), 4.1 us (A258 arm s, S75h) and 14.7 us (arm s, N75) after their start. A258's stated
  floor (6 clean pulses per phase, about 2.4 us) is therefore also the length of the unprotected start.

## 1. Overload rating

Records: A258 `run_c_{k_N0,o125_N75,o125_S75h}` (equal to A256's), A257 `run_s_o125_N13`. Each row is +62.5 A at
500 us on full load (250 A), to 620 us. "Full load" = the 50 us before the step; "overload" = the last 60 us (the
limit suspended at 517.3 / 511.6 / 505.5 / 542.3 us and stayed suspended).

| board | peak at full load (A) | peak at 125 % (A) | A per A | 200 A at |
|---|---|---|---|---|
| N0 (2.933 nH) | 147.4 | 181.2 | 0.540 | 347.3 A, 138.9 % |
| N75 (2.2 nH) | 148.1 | 182.1 | 0.544 | 345.4 A, 138.1 % |
| S75h (2.2 nH, slow devices, 125 C) | 151.0 | 184.7 | 0.539 | 340.9 A, 136.4 % |
| N13 (3.813 nH) | 146.5 | 180.4 | 0.542 | 348.7 A, 139.5 % |

Books: a phase current that runs between a fixed valley and its peak has d(peak) = 2 d(I_load / 4) - d(valley). For
+62.5 A that gives 31.25 A plus the valley's shift (0.3-0.4 A deeper), i.e. 31.5-31.7 A. The mean peak rose 32.6-33.1 A.
The 1.0-1.5 A left over (3-5 %) is the waveform's departure from a triangle; it was not traced further.

At 125 % the step itself was not the peak. In the 20 us after the step, the limit cut 10-26 pulses and the largest
turn-off was 171.8-185.3 A, equal to or below the steady overload peak (S75h 185.3 against 184.7 A).

## 2. A train while the limit is suspended

Records: A258 `run_s_pr_{N75,S75h}` (A256's count without a ceiling). In these runs the 1 MHz train from 300 us ran
unprotected until 374.5 / 371.6 us.

The bridge counts a suspended pulse as limited when the 110 A crossing plus t_ns + t_drv (1 + 10 ns) comes before
the controller's own turn-off. The recorded cuts end at 158.6-172.0 A. The replay uses the controller turn-off
current >= THR as that test.

- **Check:** the replay reproduces the recorded suspension exactly at every THR, at 210.71 / 206.18 us. Its re-arm
  is 374.54 / 372.13 us at 168 A (recorded 374.54 / 371.57 us) and up to 14 us late at 160 A.
- **From the ceiling:** with every count set to 6 at 300 us, the counts reach 0 at 2.21 / 2.17 us, the same at 160,
  165 and 168 A.

## 3. Limits

- **The rating is an extrapolation.** It runs from 125 % to 136-140 % on a relation the records hold between 100 and
  125 %. The step transient above 125 % is not measured. The conditions are one module, 25 C (S75h 125 C), and an
  overload held 120 us. The plant's inductor does not saturate; the 200 A budget stands for that.
- **The replay starts from the arm-s state.** The trains ran 10 us after the release (Vo 5.3 mV high). A train that
  starts during the release transient was not run, so the peaks in its first 2.2 us are not known.
- **Four modules were not looked at.**
