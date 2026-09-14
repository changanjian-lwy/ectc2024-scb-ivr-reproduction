# A29 results - non-paper nonideal sensitivity

LTspice completed normally. The added sensitivity values were 0.5 ns command
delay and a shared 0.5 nH + 5 mOhm input/package path. `SL2` released at
16.66747 ns. `Vds(SH2)` reached a minimum of 4.2840 V at 19.8050 ns and never
reached zero, so `SH2` remained off.

Status: **PARENT BOUNDARY FAIL; NONIDEAL COMPARISON NOT YET VALIDATED**.

Compared with A28, the minimum moved by only about -0.087 V and its time moved
by +0.401 ns. These numbers are recorded only as a sensitivity observation.
Because A28 did not achieve ZVS, A29 cannot be used to claim the effect of
hardware nonidealities on an otherwise working ZVS transition.
