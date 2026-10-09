# A184 - A183's start-up with mode S's own Ton: the loop keeps the validated seed and clamps (RESULTS)
Boundary: f8173c0 (code e1cf0a7; g0 added to the criteria block before the results). Records: release records-a184
(14 runs, log). Analysis: a184_analyze.py -> a184_summary.json. All runs from committed code, plant V5, t_il 1.0 ns.

## 0. Verdict
- **FAIL as registered on c6 at 7 runs and on c2 at 1 run. Not adopted** (decision rule: c6 fails).
- **The register works as designed.**
  - g0: on all 10 runs shared with A183, mode S is identical bit for bit up to the mode-P entry.
  - c5: after settling, mode P is the validated design (per-phase peaks within 0.33 A of the t0 = 400 records,
    four modules included).
  - c1 / c3 / c4 pass everywhere: start-up <= 144.6 A, handover <= 168.9 A, V_DS <= 34.0 V, 0 shoot-throughs,
    Vo(143.5 us) 1.032-1.129 V.
- **A181's failure is solved at 25 C.** Slow devices with L x 0.75 pass c1-c6 at three step positions:
  - start-up 135.7 A, handover 151.1 A, post-step 191.5-192.7 A;
  - handover Vo minimum 1.000 V (t0 400: 0.961 V).
  - The slow L0 board also improves (Vo minimum 0.997 V against 0.983 V).
- **c6, 25 C (N0 0.984, F0 0.987, four modules 0.982, N13 0.971 V; references 0.984-0.999 V):**
  - Mode S at 200 ns ends with valleys at +25..+47 A, while mode P regulates -15.6 A. In the first mode-P periods
    phase 1 waits for its current to fall the extra ~50 A, so the output charge falls short.
  - The loop's first Ton is the same as at 400 ns (N0 27.5 vs 27.7 ns: same seed, same kp step on +33 mV). The
    valley gap turns that Ton's shortfall below steady state into a dip:
    - shortfall -2..+3 ns (S75 -2.0, N75 +0.9, N07 +3 ns): no dip (1.000 V);
    - -5 ns (N0, F0, S0, four modules): 0.982-0.997 V;
    - -15 ns (N13): 0.971 V.
  - Peaks are not affected.
- **c6 hot (N0 0.989, S0 0.978, S75 0.975 V):** the locked mode-S trim drifts +15 / +91 / +95 mV hot. Every turn-on
  is hard, so the gates' temperature acts on every phase (t0 400: +8 / +28 / +37 mV). At entry kp x (Vo - 1 V) drives
  Ton to the 0.5x clamp for > 5 us, and Vo then undershoots. Vo(143.5) 1.126-1.129 V is inside c4's window but
  126-129 mV above 1.0 V (t0 400 hot: 57-71 mV).
- **c2: S75 at 125 C post-step 206.7 A.** This is a mode-P property, not the start-up's. The step's phase after
  phase 1's last low-side turn-off decides it: phase 0.86 -> 206.7 A here, and A181 (t0 400) 0.81 -> 202.8 A,
  0.48 -> 194.7 A, 0.15 -> 199.1 A. At 25 C the board stays <= 198.7 A at phases 0.12-0.88. So slow devices with
  L x 0.75 hold 200 A at 25 C only.

## 1. Criteria
| run | g0 | c1 start / hand (A) | c2 post (A) | c3 V_DS | c4 Vo(143.5) | c5 dev (A) | c6 Vo min (ref) |
|---|---|---|---|---|---|---|---|
| S75 25 C p0 / p1 / p2 | = | 135.7 / 151.1 | 192.5 / 191.5 / 192.7 | <= 32.8 | 1.034 | 0.31 | 1.000 (0.961) |
| S75 125 C | = | 144.6 / 142.5 | **206.7** | 33.9 | 1.129 | 0.13 | **0.975** (0.991) |
| N0 25 C | = | 124.7 / 162.6 | 184.4 | 33.7 | 1.033 | 0.17 | **0.984** (0.999) |
| S0 / N75 / N07 25 C | = | <= 139.9 / <= 151.0 | - | <= 28.6 | 1.032-1.035 | <= 0.14 | 0.997 / 1.000 / 1.000 |
| N13 / F0 25 C | = | 116.5-125.0 / 156-158 | - | <= 34.0 | 1.033 | <= 0.09 | **0.971 / 0.987** |
| N0 / S0 / F0 125 C | - | <= 131.2 / <= 151.3 | - | <= 30.7 | 1.048 / 1.126 / 1.038 | <= 0.09 / - | **0.989 / 0.978** / 0.999 (none) |
| four modules 25 C | - | 124.7 / <= 168.9 | - | <= 30.5 | 1.033 | <= 0.33 | **0.982** (0.998) |

## 2. Predictions
- g0 held (mode S never reads cfg_ton). c5 within 1.5 A held (<= 0.33).
- "Handover Vo minima within ~5 mV of the references": wrong. The prediction missed the valley gap. It held only
  where the first Ton reaches the steady one.
- Hot drift +60..+100 mV: right for the slow boards (+91 / +95), smaller for nominal (+15). "Margin >= 25 mV to
  1.17 V": 41-44 mV.

## 3. Limits
- One row (+4.8 V / 1 us) on S75 and N0. The other boards only to 500 us. Four modules only nominal.
- The c6 mechanism rests on 14 runs and their references, with no run that isolates it.

## 4. Decision (BOUNDARY Section 4)
c6 fails, so this is not adopted. Two causes, two candidate fixes:
- 25 C: seed the loop so that its first Ton equals the board's steady Ton, i.e. ton_ns = T_ss + kp (Vo(143.5) -
  1 V). This is cfg only; A185.
- Hot: hand over on Vo instead of at 144 us, so the entry state does not follow the trim's temperature drift (a
  sequencer change).
The S75 125 C post-step margin is a mode-P item and is named open.
