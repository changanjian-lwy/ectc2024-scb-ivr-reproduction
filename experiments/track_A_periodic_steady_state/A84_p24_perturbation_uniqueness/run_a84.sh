#!/bin/zsh
# A84 runs (BOUNDARY Section 4).
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
C=(--valley-mode predictive --t-d 10 --trim-gain 0.5 --no-zvs-reactive --vo-loop-ki 0.25)
python3 a84_transient.py k0_gate_a82r3 "${C[@]}" --i-target -3.75 --learn-at-restart "${F[@]}" > log_k0.txt 2>&1 &
python3 a84_transient.py k1_5pct_learn_kick "${C[@]}" --i-target -6.25 --learn-at-restart --kick-t 250 "${F[@]}" > log_k1.txt 2>&1 &
python3 a84_transient.py k2_5pct_nolearn_kick "${C[@]}" --i-target -6.25 --kick-t 250 "${F[@]}" > log_k2.txt 2>&1 &
python3 a84_transient.py k3_3pct_learn_kick "${C[@]}" --i-target -3.75 --learn-at-restart --kick-t 250 "${F[@]}" > log_k3.txt 2>&1 &
python3 a84_transient.py k4_3pct_nolearn_kick "${C[@]}" --i-target -3.75 --kick-t 250 "${F[@]}" > log_k4.txt 2>&1 &
wait
grep -h 'end:' log_k*.txt
