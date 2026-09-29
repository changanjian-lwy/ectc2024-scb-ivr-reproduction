#!/bin/zsh
# A78 runs (BOUNDARY Section 5): adopted A76 controller, negative-current target sweep.
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
C=(--valley-mode predictive --t-d 10 --trim-gain 0.5)
python3 a78_transient.py r0_gate_a76r1 "${C[@]}" "${F[@]}" > log_r0.txt 2>&1 &
i=1
for it in -1.25 -2.5 -3.75 -5.0 -6.25 -9.375 -12.5; do
  python3 a78_transient.py r${i}_itarget_${it} "${C[@]}" --no-zvs-reactive --i-target $it "${F[@]}" > log_r${i}.txt 2>&1 &
  i=$((i+1))
done
wait
grep -h 'end:' log_r*.txt
