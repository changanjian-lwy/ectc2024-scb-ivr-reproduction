# Step 33 - Track-A A01 first periodic residual

A01 is the first main-line single-module/four-phase periodic-orbit attempt after
separating zero startup. It uses the P24 2% source-native branch, 5 MHz and one
250-W module belonging to the four-module 1-kW design point. No parameter was
fitted after seeing the output.

`36/24/12 V`, `Vout=1 V` and zero phase currents were used only as the first
slow-state seed. The phase-1-origin switching-node seed was derived from the
same topology so device Coss did not begin in a contradictory state.

The 200-ns map does not close. Residuals are:

`[dVC1,dVC2,dVC3,dVout] = [+0.3882,+0.2317,-0.2522,-4.3868] mV`

`[diL1,diL2,diL3,diL4] = [-0.4190,+4.5928,+40.4428,+85.0041] A`

Status: **VALID_FIRST_SEED_RUN; PERIODIC_CLOSURE_FAILED**.

The result validates the residual harness because it identifies phases 3 and 4
as the dominant state mismatch instead of accepting the comparatively small
capacitor/output drift. It does not yet validate the P24-derived symmetric gate
controller: phase-1 minimum current is -3.337 A versus a 2.5-A target (2% of
125 A), so the behavioral zero/negative release needs an event latch rather than
a memoryless voltage/current expression.

Next change must be controller implementation only: replace each memoryless
low-side expression with a latched physical-event state while retaining the same
P24 2% threshold and initial seed. Only after that controller boundary passes is
long-run settling or a periodic shooting iteration meaningful.
