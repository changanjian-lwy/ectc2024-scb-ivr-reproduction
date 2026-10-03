# A130 - Line-slope boundary of vff + gth 100 (RESULTS)
Boundary: 91118b0. Records: cosim/run_y130_*.json (10), a130_summary.json. Conditions: 2.5 MHz A124 design, vff gth 100, cosim, step phases t_us 800 / 800.33.

## 0. Verdict
- All five new rows pass 200 A at both phases: -8 V/6 us 192.2 / 191.6 A, -8 V/7.5 us 180.0 / 178.5 A, +4.8 V/2 us 177.9 / 180.3 A, +4.8 V/3 us 176.9 / 178.9 A, +8 V/10 us 198.3 / 195.7 A (marginal, 1.7 A margin).
- Bus-slew spec of the adopted design (fastest passing slew, with A129's rows): |step| <= 4.8 V: >= 1 us (<= 4.8 V/us, rise and fall); -8 V: >= 6 us (<= 1.33 V/us; 5 us = 208 A fails); +8 V: >= 10 us (<= 0.8 V/us, marginal; faster rises untested).
- The -8 V/5 us -> 6 us edge sits between 208 A and 192 A; -8 V/6 us is 7.8 A under the limit (not "marginal" by the 7 A rule, but thin).
- D63 (gate never opens in these rows) was within -8..+3 A of cosim for the rises and 4 A (7.5 us) to 14 A (6 us) low for the -8 V falls, as expected; all peaks inside A125's M80 and G80 bands.
- Phase spread 0.6-2.6 A (inside A129's 2-7 A noise floor). Late fires 0-2 per run, no runaway.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | both phases <= 200 A; marginal 193-200 A | 4 pass, +8 V/10 us marginal (worst 198.3 A) |
| 2 | late <= 100, no runaway | met (late <= 2) |
| 3 | monotone spec, no hole | met: -8 V 5 us fail, 6/7.5/10 us pass; +4.8 V 1/2/3/5 us pass |

## 2. Limits
- Only +-4.8 V and +-8 V amplitudes; 8 V rises below 10 us and 8 V falls between 5 and 6 us not resolved.
- +8 V/10 us has 1.7 A margin, inside the 2-7 A noise floor: treat 10 us as the edge, not a safe value.
- Peak vs slew is not guaranteed monotone near 200 A beyond two phases; a spec with margin would use 7.5 us (falls) and a slower rise.
