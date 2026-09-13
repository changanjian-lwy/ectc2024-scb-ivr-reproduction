# Common physics layer

These relations do not change when a component or topology module is replaced.

## Energy-storage elements

`vL = L * diL/dt`

`iC = C * dvC/dt`

`EL = 0.5 * L * iL^2`

`EC = integral(v * C(v) dv)`; `0.5*C*V^2` is used only for constant C.

## Periodic steady state

`integral_0^T(vL dt) = 0`

`integral_0^T(iC dt) = 0`

## Loss interfaces

`Pcond = average(i^2 * R)`

`Esw = integral(vDS * iD dt)` over one switching event.

`Psw = fsw * sum(Esw)`.

## ZVS feasibility boundary

The negative inductor-current state must provide enough commutation energy
and the transition must finish before the commanded high-side turn-on:

`0.5*L*Ineg^2 >= Ecomm(CH, CL, Coss(V), node voltages)`

`tcomm <= available dead time`.

The topology module determines which capacitors participate and their initial
and final voltages. A component module supplies `Coss(V)`, resistance and
delay data. Neither is allowed to alter the equations above.
