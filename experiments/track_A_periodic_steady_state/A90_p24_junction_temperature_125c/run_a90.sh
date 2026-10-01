#!/bin/zsh
# A90 runs (BOUNDARY Section 4).
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
C=(--valley-mode predictive --trim-gain 0.5 --no-zvs-reactive --vo-loop-ki 0.25 --learn-at-restart --nonlinear-coss --t-d 10 --rev-drop --low-mode predictive)
python3 a90_transient.py r0_gate_a88r1 "${C[@]}" --tj 25 --i-target -3.75 "${F[@]}" > log_r0.txt 2>&1 &
python3 a90_transient.py r1_3pct_125c "${C[@]}" --tj 125 --i-target -3.75 "${F[@]}" > log_r1.txt 2>&1 &
python3 a90_transient.py r2_2pct_125c "${C[@]}" --tj 125 --i-target -2.5 "${F[@]}" > log_r2.txt 2>&1 &
python3 a90_transient.py r3_5pct_125c "${C[@]}" --tj 125 --i-target -6.25 "${F[@]}" > log_r3.txt 2>&1 &
python3 a90_transient.py r4_7p5pct_125c "${C[@]}" --tj 125 --i-target -9.375 "${F[@]}" > log_r4.txt 2>&1 &
wait
grep -h 'end:' log_r*.txt
