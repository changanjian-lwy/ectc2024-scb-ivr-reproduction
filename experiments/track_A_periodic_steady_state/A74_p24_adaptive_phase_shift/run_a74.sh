#!/bin/zsh
# A74 runs (BOUNDARY Section 5): run 0 = A73 run 5 replayed (regression gate), runs 1-3 = the 2 x 2 design.
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
python3 a74_transient.py r0_fixed_rs20 --t-restart-high 20 "${F[@]}" > log_r0.txt 2>&1 &
python3 a74_transient.py r1_adaptive_rs20 --t-restart-high 20 --adaptive-shift "${F[@]}" > log_r1.txt 2>&1 &
python3 a74_transient.py r2_adaptive_rs60 --t-restart-high 60 --adaptive-shift "${F[@]}" > log_r2.txt 2>&1 &
python3 a74_transient.py r3_fixed_rs60 --t-restart-high 60 "${F[@]}" > log_r3.txt 2>&1 &
wait
tail -n 2 log_r*.txt
