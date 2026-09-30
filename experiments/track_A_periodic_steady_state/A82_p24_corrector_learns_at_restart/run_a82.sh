#!/bin/zsh
# A82 runs (BOUNDARY Section 1).
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
C=(--valley-mode predictive --t-d 10 --trim-gain 0.5 --no-zvs-reactive)
python3 a82_transient.py r0_gate_a79r2 "${C[@]}" --i-target -6.25 --vo-loop-ki 1.0 "${F[@]}" > log_r0.txt 2>&1 &
python3 a82_transient.py r1_5pct_ki1_learn "${C[@]}" --i-target -6.25 --vo-loop-ki 1.0 --learn-at-restart "${F[@]}" > log_r1.txt 2>&1 &
python3 a82_transient.py r2_4pct_learn "${C[@]}" --i-target -5.0 --vo-loop-ki 0.25 --learn-at-restart "${F[@]}" > log_r2.txt 2>&1 &
python3 a82_transient.py r3_3pct_learn "${C[@]}" --i-target -3.75 --vo-loop-ki 0.25 --learn-at-restart "${F[@]}" > log_r3.txt 2>&1 &
python3 a82_transient.py r4_2p5pct_learn "${C[@]}" --i-target -3.125 --vo-loop-ki 0.25 --learn-at-restart "${F[@]}" > log_r4.txt 2>&1 &
python3 a82_transient.py r5_2pct_learn "${C[@]}" --i-target -2.5 --vo-loop-ki 0.25 --learn-at-restart "${F[@]}" > log_r5.txt 2>&1 &
python3 a82_transient.py r6_3pct_nolearn "${C[@]}" --i-target -3.75 --vo-loop-ki 0.25 "${F[@]}" > log_r6.txt 2>&1 &
wait
grep -h 'end:' log_r*.txt
