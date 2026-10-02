# A112 - the 20% and 25% negative-current designs on the standard matrix (BOUNDARY)

Track A, main line. **Written before any A112 run.**

**The two candidates (A110):** the adopted single module (A105's I2 with
`slot_lo`) with the negative-current target at:
- **20%:** the efficiency optimum, 90.17%, high side at 2.3-3.0 V;
- **25%:** practical high-side zero voltage, −0.16 to +0.86 V, 90.14%.

**The 16 rows** of the shared standard matrix
(`scb_ivr.cosim.matrix.ROWS`) for each: 32 runs (`make_cfgs.py`).

**One factor against the 5% design's matrix** (A105 i2_<row>, A106
pi100_<row>): the target.

## 1. Registered predictions and criteria

1. **p20_n0 and p25_n0** are A110's n20 and n25 configurations
   unchanged. They must be identical to them in every record except
   `wall_s` and `provenance`.
2. **No overlap in any of the 32 runs.**
3. **Peak current. A higher target raises the steady peak:** 151 A
   (20%) and 158 A (25%) against 134 A (5%), +17 / +24 A. Two windows:
   - **the run's peak**, which includes the handover to mode P: 20%
     ≤ 200 A; 25% ≥ 204 A in every row (A110's handover peak, common to
     all rows). The 25% handover peak is a known open item, not graded
     per row;
   - **after 150 µs** (the recorded events: steady state and steps):
     ≤ 200 A in every row except the line steps, predicted as the 5%
     single module's peak after the same step plus 17 / 24 A, ±10 A:

     | row | 5% (A108 / A106) | 20% | 25% |
     |---|---|---|---|
     | l_p48_1us | 203 A | 220 A | 227 A |
     | l_m48_1us | 190 A | 207 A | 214 A |
     | l_p48_10us | 166 A | 183 A | 190 A |
     | l_m48_10us | 138 A | 155 A | 162 A |

     So the 200 A limit is crossed by the 1 µs steps in both designs.
     The slower ones stay inside it.
4. **The high side's turn-on keeps its level** under driver mismatch and
   jitter: each phase's mean within ±0.5 V of its design's n0 (m and j
   rows). The low side's turn-on V_DS ≤ 0 in the m rows.
5. **Turn-off spread under jitter** (j30, j100) within the 5% design's
   × (1 ± 0.5).
6. **Load steps** (±25, ±62.5 A): extreme within ±30% of the 5%
   design's, and recovered (finite).
7. **Line steps:** recovered (finite). Vo extreme within ±30% of the 5%
   design's.

## 2. What stays assumed

- **As A110:** 25 C; datasheet Coss; D62 middle case for the efficiency
  quoted.
- **The driver mismatch** is the same on every phase (the matrix's
  definition).
