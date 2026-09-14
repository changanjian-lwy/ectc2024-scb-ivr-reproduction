# Four-phase local-timeline rebuild

## Reason for rebuild

The A28-A32 sequence mixed two different clocks:

1. the global four-phase origins `0/50/100/150 ns`;
2. physical event boundaries such as current zero, negative-current target and
   switch `Vds=0`.

This allowed phase 2 to begin with a low-side latch at global `t=0` without
first proving which local P24 interval phase 2 occupied. The resulting 2%
threshold was initially missed and the ZVS opportunity appeared near 17-26 ns
instead of the nominal phase-2 origin at 50 ns.

## Locked time coordinates

For `T=200 ns` and `nP=4`, phase `k` uses

`tau_k = (t-(k-1)T/nP) mod T`.

At global `t=0`:

| Phase | Nominal origin | Local cycle coordinate | Electrical mode |
|---:|---:|---:|---|
| 1 | 0 ns | 0 ns | requires selected reference event |
| 2 | 50 ns | 150 ns | unresolved until prior-cycle event history is supplied |
| 3 | 100 ns | 100 ns | unresolved until prior-cycle event history is supplied |
| 4 | 150 ns | 50 ns | unresolved until prior-cycle event history is supplied |

The coordinates are mathematical facts. The mode column cannot be filled from
time alone because P24 does not publish fixed durations for intervals 2 and 3.

## Compiler rule

- Fixed clock: phase origin and P24 high-side on-time end only.
- Physical events: low-side Vds zero, current zero, negative-current target,
  high-side Vds zero and ZVS admission.
- A physical event may occur near a nominal origin, but the origin cannot
  substitute for the event.
- Each phase calls the same local state machine with a rotated event history;
  no phase-specific absolute-time release rule is allowed.

## Old-netlist finding

The A25-A32 family contains absolute global-time guards such as
`time>TON`, `time>PHASE+TON` and `time>2*PHASE+TON` inside per-phase low-side
machines. These files remain valid diagnostic history, but they are not the
compiler source for the rebuilt controller.

## Next executable gate

Before another four-phase electrical run, construct a symbolic circular event
history for all four phases and prove:

1. every phase has one high-side origin per 200 ns;
2. every low-side release follows its own negative-current event;
3. every high-side admission follows its own Vds-zero event;
4. no phase mode is inferred solely from `tau_k`;
5. the initial state is a periodic fixed point, not four independent guesses.
