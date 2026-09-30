#!/bin/zsh
# A86 amendment 7: runs n6-n8.
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
C=(--valley-mode predictive --t-d 10 --trim-gain 0.5 --no-zvs-reactive --vo-loop-ki 0.25 --learn-at-restart --nonlinear-coss)
python3 a86_transient.py n6_1pct_nl "${C[@]}" --i-target -1.25 "${F[@]}" > log_n6.txt 2>&1 &
python3 a86_transient.py n7_1p5pct_nl "${C[@]}" --i-target -1.875 "${F[@]}" > log_n7.txt 2>&1 &
python3 a86_transient.py n8_2pct_nl_kick "${C[@]}" --i-target -2.5 --kick-t 250 "${F[@]}" > log_n8.txt 2>&1 &
wait
grep -h 'end:' log_n6.txt log_n7.txt log_n8.txt
