#!/bin/zsh
# A79 amendment 8: runs 3-4 at -9.375 A (7.5%).
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
C=(--valley-mode predictive --t-d 10 --trim-gain 0.5 --no-zvs-reactive --i-target -9.375)
python3 a79_transient.py r3_itgt9p375_ki0p25 "${C[@]}" --vo-loop-ki 0.25 "${F[@]}" > log_r3.txt 2>&1 &
python3 a79_transient.py r4_itgt9p375_ki1p0 "${C[@]}" --vo-loop-ki 1.0 "${F[@]}" > log_r4.txt 2>&1 &
wait
grep -h 'end:' log_r3.txt log_r4.txt
