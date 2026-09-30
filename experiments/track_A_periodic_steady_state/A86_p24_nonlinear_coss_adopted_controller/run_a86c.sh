#!/bin/zsh
# A86 amendment 8: runs e1, e2 (D44's L2 equivalent-linear capacitance) and n0b (gate after the CLI change).
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
C=(--valley-mode predictive --t-d 10 --trim-gain 0.5 --no-zvs-reactive --vo-loop-ki 0.25 --learn-at-restart)
L2=(--c-high-pf 1796.883230828922 --c-low-pf 2424.489989320878)
python3 a86_transient.py e1_3pct_L2 "${C[@]}" "${L2[@]}" --i-target -3.75 "${F[@]}" > log_e1.txt 2>&1 &
python3 a86_transient.py e2_2pct_L2 "${C[@]}" "${L2[@]}" --i-target -2.5 "${F[@]}" > log_e2.txt 2>&1 &
python3 a86_transient.py n0b_gate_a82r3 "${C[@]}" --i-target -3.75 "${F[@]}" > log_n0b.txt 2>&1 &
wait
grep -h 'end:' log_e1.txt log_e2.txt log_n0b.txt
