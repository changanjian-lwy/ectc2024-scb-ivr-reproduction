#!/bin/zsh
# A74 BOUNDARY Section 8: runs 0 and 1 rerun with the diagnostic log (must be bit-identical to runs 0 and 1).
cd "${0:A:h}" || exit 1
F=(--stall-periods 20 --level-events --t-restart-low 400 --diode-check --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61)
python3 a74_transient.py r0d_fixed_rs20_diag --t-restart-high 20 "${F[@]}" > log_r0d.txt 2>&1 &
python3 a74_transient.py r1d_adaptive_rs20_diag --t-restart-high 20 --adaptive-shift "${F[@]}" > log_r1d.txt 2>&1 &
wait
tail -n 2 log_r0d.txt log_r1d.txt
