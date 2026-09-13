# A02 results - device-Coss stage revalidation

## Result summary

All runs use `CH_DEVICE=385 pF`, `CL_DEVICE=770 pF` and zero added snubber.
No topology, timing, initial-state or negative-current boundary was tuned.

| Stage | Result after adding/calling device Coss | Claim boundary |
|---|---|---|
| P24 Mode 1 energy interval | Remains successful; `IL1,max=124.932724 A`, exactly the no-Coss value at reported precision | Coss is clamped during the already-ON state; this is not a switching-transition test |
| P24 t1 commutation | A finite low-side-node transition appears; `V(x1)` reaches zero at `0.110525 ns`, with `IL1=125.308 A` | Device-only scalar Coss; no external snubber/dead time |
| P24 interval 2 | Low-side ZVS event remains at `0.110525 ns`; `IL1` reaches zero at `152.492 ns` | Local interval only; inherited phase-2 current is not a periodic solution |
| P24 1% negative branch | Fails high-side ZVS; post-release minimum high-side Vds is `9.2566 V` | Correctly retained failure, not repaired by changing Coss or threshold |
| P25 5% mapped branch | Still fails high-side ZVS; minimum high-side Vds is `3.8744 V` | Cross-paper sensitivity branch, not P24 truth |
| Calibrated 8% model branch | Local high-side ZVS exit remains successful; high-side Vds reaches zero at `16.7732 ns` and gate rises about `0.000402 ns` later | Model calibration only; 8% is not a published P24 value |

## Mode-1 controlled difference

Compared with R04D0, A02-1 changes only device capacitance:

| Quantity | No-Coss R04D0 | Device-Coss A02-1 | Difference |
|---|---:|---:|---:|
| `IL1` near `Ton` | 124.782991351 A | 124.782994832 A | +3.481 uA |
| `IL1,max` | 124.932723999 A | 124.932723999 A | 0 A |
| `IL2` near `Ton` | -11.3505529996 A | -11.3505528267 A | +0.173 uA |
| `VC1,end` | 36.0193109995 V | 36.0193106287 V | -0.371 uV |
| C1 transferred charge | 1.03897924816 uC | 1.03896428595 uC | -14.962 pC (-0.00144%) |

The Mode-1 change is numerically negligible, as expected: the conducting
switches clamp their parallel capacitances. Coss becomes decisive only when a
switch turns off and inductor current must move charge between high- and
low-side capacitances.

## Main conclusion

Adding device Coss does not invalidate the previously verified Mode-1 energy
transfer. It replaces the ideal instantaneous t1 handoff with a finite
commutation interval and makes the negative-current requirement observable.
Under this scalar GS61008T model, the P24 1%-2% branch is insufficient and the
P25 5% mapped branch is also insufficient; only the separately calibrated 8%
local model branch completes the tested high-side ZVS exit. This does not
authorize changing the P24 boundary to 8% in the main reproduction.
