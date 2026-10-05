# A147 - a learned anomaly detector against the hand-written oracles (RESULTS)
Boundary: d5bf5af. Outputs: a147_summary.json (registered labels), a147_summary_guard2.json (post hoc, see 2),
a147_inspect*.json (a147_inspect.py), a147_ae.npz (network, scaling, thresholds, PCA). Features: tmp/a147
(a147_features.py, 18 s).

## 0. Verdict
- **On the classes the oracles know, the CNN adds nothing.** AUROC of oracle-defect windows against clean test
  windows: AE 1.000, PCA 0.999, z-score 0.999. The z-score (no model) has the fewest false alarms: 0.3 % against
  the AE's 1.4 %. Duplicates, order errors and spikes are gross; comparing with the median is enough. This is a
  negative result for the CNN.
- **The independent detectors point at a property no oracle checks: loss of ZVS (valley current above the +2 A
  floor).**
  - It is 78 % of the AE's unexplained flags (1437 of 1844 windows) and 100 % of the z-score's (1095).
  - The 20 highest AE flags are 17 of this kind plus 3 labelling artefacts (registered labels); with the corrected
    labels, all 20 are of this kind.
  - It is in the frozen design. After the in-spec +4.8 V / 1 us step, phase 1's low side turns off at +12..+15 A for
    ~13 us (A143 K 4 record; 24 periods). The next phase-1 turn-on is hard: V_DS 17-19 V against 3.9 V before the
    step (correlation 0.98).
  - That is A144's dV 19.1 V, whose ring puts SH2 at 52-58 V (A144, A145). **The binding line-step overshoot of the
    package layer is a ZVS loss, and no check in the project watches the valley's sign.**
- **What is the CNN's own:** 1149 flags the z-score does not raise. 57 % are window-edge artefacts (zero padding;
  the score should skip the edges). The rest are mostly valley excursions near the z threshold and deep phase-2-4
  valleys (-80 A) of pre-A143 designs, A143's documented mechanism, also unchecked.
- **A145's finite edges cause no false alarms** (1.1 %): a physics change inside the normal range is not flagged.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | false alarms <= 2 % | PASS: 1.4 % (A139 1.0, A142 2.0, A143 1.0, A145 1.1 %) |
| 2 | AUROC >= 0.95 and >= baseline + 0.02 | FAIL: 1.000 vs 0.999 / 0.999 |
| 3 | runs flagged: storm, runaway, regulation >= 90 %, defect >= 80 % | FAIL as registered: storm 37/39, runaway 12/14, regulation 27/27, defect 650/650. The 4 misses happen before the analysed window (A133 pl07: 404 A at start-up; A136 m3n: late fires at the handover); inside it, all are flagged |
| 4 | top 20 unexplained classified, (c) <= 10 | PASS: 17 (a) ZVS loss after line steps, 3 (c) |

Note on (c): an order oracle event is stamped at the later turn-on, which starts the next period, so it fell on
the window's open end. With 2 periods of guard (post hoc) the AUROC and false alarms are unchanged.

Predictions:
- AUROC 0.92 / 0.88 / 0.85: wrong, all ~1.0.
- False alarms 2-3 %: 1.4 %.
- Run level 100 / ~90 / ~75 %: 95 / 86 / 100 / 100 %.
- Unexplained flags mostly (b), with 0-2 (a): wrong. Nearly all are one unchecked defect class.

## 2. Decision (registered rule: any (a) -> reopen it as a defect) and limits
- Reopened as A148: keep phase 1's valley below the floor through rising line steps (the target of the RL experiment;
  the metric is the valley sign / turn-on V_DS after the step).
- Until then, the verification claim is narrowed. The oracles check timing, order, duplicates and spikes, not ZVS.
  A ZVS oracle (mode P low-off current <= floor + margin) joins the checks with A148.
- The AE is not kept as a monitor: the z-score plus the oracles (and the ZVS oracle) find the same.
- Limits:
  - One design family (t0 400 ns, single module), mode P only; start-up and handover are outside the window.
  - Labels come from the oracles, so the AUROC can only measure known classes.
  - Edge artefacts in the AE score; a 64-period window (~32 us).
