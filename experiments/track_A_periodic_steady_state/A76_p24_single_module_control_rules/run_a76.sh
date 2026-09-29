#!/bin/zsh
# A76 runs (BOUNDARY Section 5). P24, A75 settings: fixed shifts, restart 20 ns.
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
P=(--valley-mode predictive)
python3 a76_transient.py r0_gate_pred_td10 "${P[@]}" --t-d 10 "${F[@]}" > log_r0.txt 2>&1 &
python3 a76_transient.py r1_pred_td10_trim "${P[@]}" --t-d 10 --trim-gain 0.5 "${F[@]}" > log_r1.txt 2>&1 &
python3 a76_transient.py r2_pred_td18_trim "${P[@]}" --t-d 18 --trim-gain 0.5 "${F[@]}" > log_r2.txt 2>&1 &
python3 a76_transient.py r3_pred_td18_trim_nozvs "${P[@]}" --t-d 18 --trim-gain 0.5 --no-zvs-reactive "${F[@]}" > log_r3.txt 2>&1 &
python3 a76_transient.py r4_react_td0_qual --qualify-current "${F[@]}" > log_r4.txt 2>&1 &
python3 a76_transient.py r5_pred_td0_qual "${P[@]}" --qualify-current "${F[@]}" > log_r5.txt 2>&1 &
python3 a76_transient.py r6_full_td10 "${P[@]}" --t-d 10 --trim-gain 0.5 --qualify-current --no-zvs-reactive "${F[@]}" > log_r6.txt 2>&1 &
python3 a76_transient.py r7_full_td18 "${P[@]}" --t-d 18 --trim-gain 0.5 --qualify-current --no-zvs-reactive "${F[@]}" > log_r7.txt 2>&1 &
wait
grep -h 'end:' log_r*.txt
