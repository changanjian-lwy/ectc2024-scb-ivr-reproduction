# P24 four-phase symbolic event ring

## Reused local sequence

Every phase uses this identical event order:

`QHk ON -> QHk OFF -> Vds(QLk)=0 -> QLk ON -> iLk=0 ->`
`iLk=-Ineg -> QLk OFF -> Vds(QHk)=0 -> QHk ON`.

Only the first high-side on-time end is fixed by P24 Eq. (3). All other arrows
are physical-event transitions.

## Four rotated instances

| Active phase | High side | Own commutating low side | P24-explicit adjacent support in interval 1 | Next active phase |
|---:|---|---|---|---:|
| 1 | QH1 | QL1 | QS2 | 2 |
| 2 | QH2 | QL2 | QS3 | 3 |
| 3 | QH3 | QL3 | QS4 | 4 |
| 4 | QH4 | QL4 | QS1 | 1 |

`QS` is retained exactly as P24's printed low-side notation in the symbolic
source layer. A later topology adapter may establish whether each `QSk` is the
same physical position called `QLk` elsewhere; it may not assume the alias
silently.

## What this resolves

- There is one state-machine definition, instantiated four times.
- Phase number changes component labels, not transition physics.
- A fixed 50 ns origin cannot skip current-zero, negative-target, low-side-off
  or high-side-Vds-zero events.
- The A25-A32 absolute-time low-side rules are diagnostic history only.

## Remaining blocker before electrical compilation

The symbolic ring still cannot assign the full simultaneous four-phase gate
vector because P24 explicitly names `QH1` and `QS2` in interval 1 but leaves
the other low-side commands unspecified. P25 supplies an all-inactive-low
answer for its own topology, but that is a separate extension branch. The
compiler must therefore produce two truth-table branches and must preserve the
`QS`/`QL` alias question until the Fig. 3 connectivity adapter verifies it.
