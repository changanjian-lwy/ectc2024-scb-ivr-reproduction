# Negative-current margin versus ZVS/timing conflict

## Observed conflict

Increasing the negative-current target increases the energy/charge available
to commutate switch output capacitances and therefore improves local ZVS
margin. The same change also:

- increases reverse current and reverse-conduction loss;
- lengthens the negative-current build interval;
- increases RMS current and conduction loss;
- can push the next high-side readiness event beyond its nominal `T/nP` slot;
- makes 5 MHz uniform four-phase timing harder to satisfy.

In the current constant-Coss diagnostic, the P24 2% local event does not reach
high-side zero voltage, while the labelled P25 9% extension does. Conversely,
the 9% event ring produces an approximately 211.7 ns nonuniform orbit instead
of the P24 200 ns period and 50 ns phase spacing.

## Design statement

The negative-current fraction is not a free knob to maximize. It is the
smallest value that must satisfy ZVS across device/timing variation while also
meeting period, phase-slot, RMS-current and loss constraints. P24 1-2% and P25
5-10% remain separate source branches.

## Controller consequence

The recommended controller is hybrid:

1. high-side conduction ends after the fixed relative `TON`;
2. peak-current error is measured at that instant, not used to extend `TON`;
3. commutation and low-side transitions remain event-driven;
4. the next high side requires both its nominal phase slot and `Vds=0`;
5. a missed slot is reported and blocks hard turn-on.
