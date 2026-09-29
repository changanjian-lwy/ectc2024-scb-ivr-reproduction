#!/bin/zsh
# A79 runs (BOUNDARY Sections 4 and 7): adopted A76 controller at -6.25 A, output-voltage loop gain sweep.
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
C=(--valley-mode predictive --t-d 10 --trim-gain 0.5 --no-zvs-reactive --i-target -6.25)
python3 a79_transient.py r0_gate_a78r5 "${C[@]}" "${F[@]}" > log_r0.txt 2>&1 &
python3 a79_transient.py r1_ki0p25 "${C[@]}" --vo-loop-ki 0.25 "${F[@]}" > log_r1.txt 2>&1 &
python3 a79_transient.py r2_ki1p0 "${C[@]}" --vo-loop-ki 1.0 "${F[@]}" > log_r2.txt 2>&1 &
wait
grep -h 'end:' log_r*.txt
