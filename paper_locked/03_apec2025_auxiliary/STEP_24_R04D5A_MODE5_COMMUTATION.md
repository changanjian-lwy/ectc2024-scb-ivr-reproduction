# Step 24 - R04D5A P25 Mode-5 commutation

## Boundary confirmation

P25 Mode 4 ends at `t4` when the controller decides to turn SL2 off, while
Mode 5 says SL2 physically turns off at `t5`. The paper reports no `t5-t4`
delay. This first baseline explicitly uses `t5=t4`; the missing delay remains
an unresolved controller parameter.

Mode 5 runs from physical `SL2 OFF` to `Vds(SH2)=0` and `SH2 ON`. Mode 5-prime
is minimized with ideal event timing because no dead time is reported.

## Device plug-in and result

The P25 12 V, three-phase capacitor ratings give `VCS1=8 V`, `VCS2=4 V`, so
the phase-2 commutation voltage is 4 V. The unreported CH2/CL2 values are
represented by the GS61008T time-equivalent scalar: 385 pF high side and
770 pF for two parallel low-side devices.

- Start current from R04D4A: -2.22231 A.
- High-side Vds reaches zero after 2.09454 ns.
- Current at zero Vds: -2.12546 A.
- SH2 gate event: 2.09471 ns, current -2.12544 A.

The ideal device-plug-in branch reaches the Mode-5 ZVS exit. It does not claim
the authors' unreported snubber, delay or Mode-5-prime duration.
