# A25 results - first full low-side-latch integration

## Passed events before the first failure

- At the established 2 ps initial sample, `SL2`, `SL3` and `SL4` are ON as
  required by the P25 all-inactive-low Mode-1 rule.
- No same-leg high/low command overlap is detected in any of the four legs.
- `SL1` is admitted at 16.812 ns with its switch node at -63.6 mV.
- `SL2` reaches the 9% target and releases at 23.737 ns with
  `iL2=-11.252 A`.

## First failed boundary

The first failure occurs at the fixed phase-2 high-side command:

| Event | Time | Required | Simulated |
|---|---:|---:|---:|
| `SH2` fixed rising command | 50.000 ns | `Vds(SH2)=0` before turn-on | 21.562 V |

Therefore A25 stops its success claim at 23.737 ns. The phase-2 high side is
commanded while substantial voltage remains across it, so this is not ZVS.

Later diagnostics are retained but cannot override the first failure:

- `SH3` at 100 ns: `Vds=21.600 V`, fail;
- `SH4` at 150 ns: `Vds=7.237 V`, fail;
- next `SH1` at 200 ns: `Vds=2.319 V`, fail.

All four low-side state machines do reach their programmed 9% releases and
post-high low-side admissions, but the locked fixed high-side schedule is not
compatible with the resulting event timing/commutation under this state.

## Result and module diagnosis

**A25 fails first in the high-side scheduler/ZVS-readiness interface, not in
the low-side latch module.** This is precisely the separation the modular test
was intended to expose.

No phase offset, high-side pulse, threshold, component value, initial state or
output boundary was changed after the failure. The next justified module is a
ZVS-readiness gate in front of each fixed high-side request: it may allow a
request only after the corresponding `Vds` reaches zero. Whether a maximum
delay/skip policy is needed is not specified by P24/P25 and must remain an
explicit controller assumption or a question for the authors.
