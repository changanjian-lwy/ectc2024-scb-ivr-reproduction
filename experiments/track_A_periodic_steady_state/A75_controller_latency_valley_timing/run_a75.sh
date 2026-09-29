#!/bin/zsh
# A75 runs (BOUNDARY Sections 5 and 9). P24: fixed shifts, restart 20 ns (A74 run 0 settings) x latency x valley mode.
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
python3 a75_transient.py r0_reactive_td0 "${F[@]}" > log_r0.txt 2>&1 &
python3 a75_transient.py r1_reactive_td5 --t-d 5 "${F[@]}" > log_r1.txt 2>&1 &
python3 a75_transient.py r2_reactive_td10 --t-d 10 "${F[@]}" > log_r2.txt 2>&1 &
python3 a75_transient.py r3_reactive_td18 --t-d 18 "${F[@]}" > log_r3.txt 2>&1 &
python3 a75_transient.py r4_predictive_td0 --valley-mode predictive "${F[@]}" > log_r4.txt 2>&1 &
python3 a75_transient.py r5_predictive_td5 --valley-mode predictive --t-d 5 "${F[@]}" > log_r5.txt 2>&1 &
python3 a75_transient.py r6_predictive_td10 --valley-mode predictive --t-d 10 "${F[@]}" > log_r6.txt 2>&1 &
python3 a75_transient.py r7_predictive_td18 --valley-mode predictive --t-d 18 "${F[@]}" > log_r7.txt 2>&1 &
# P25 control run: A73 run 7's sequence with 1EDBx275F latency
python3 a75_transient.py r8_p25_reactive_td45 --preset p25 --t-ramp 46 --t-load 96 --t-hand 96 --t-end 696 --diode-check --t-d 45 > log_r8.txt 2>&1 &
wait
tail -n 2 log_r*.txt
