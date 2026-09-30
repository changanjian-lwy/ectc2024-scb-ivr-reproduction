#!/bin/zsh
# A86 runs (BOUNDARY Section 4): adopted controller (learn at restart), ki 0.25, zero start; nonlinear Coss.
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
C=(--valley-mode predictive --t-d 10 --trim-gain 0.5 --no-zvs-reactive --vo-loop-ki 0.25 --learn-at-restart)
python3 a86_transient.py n0_gate_a82r3 "${C[@]}" --i-target -3.75 "${F[@]}" > log_n0.txt 2>&1 &
python3 a86_transient.py n1_2pct_nl "${C[@]}" --i-target -2.5 --nonlinear-coss "${F[@]}" > log_n1.txt 2>&1 &
python3 a86_transient.py n2_2p5pct_nl "${C[@]}" --i-target -3.125 --nonlinear-coss "${F[@]}" > log_n2.txt 2>&1 &
python3 a86_transient.py n3_3pct_nl "${C[@]}" --i-target -3.75 --nonlinear-coss "${F[@]}" > log_n3.txt 2>&1 &
python3 a86_transient.py n4_5pct_nl "${C[@]}" --i-target -6.25 --nonlinear-coss "${F[@]}" > log_n4.txt 2>&1 &
python3 a86_transient.py n5_7p5pct_nl "${C[@]}" --i-target -9.375 --nonlinear-coss "${F[@]}" > log_n5.txt 2>&1 &
wait
grep -h 'end:' log_n*.txt
