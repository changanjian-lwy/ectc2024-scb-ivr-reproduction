Subject: Follow-up on today's meeting - EPC2067 candidate rerun, a scaling law across three experiments, and a possible explanation for the missing 48V data

Hi Mihai,

Thank you for the time today. A quick written summary of what we discussed, plus what we followed up on overnight, so it's all in one place.

## From today's discussion

- We now understand the 2025 paper's role differently than before: it's there to help understand causal trends and mechanisms in the 2024 design, not to supply exact numbers we can drop into the 2024 model. We've been treating some of its values (device Coss, parallel counts) as more directly portable than they should be, and are correcting that.
- On Coss specifically: the "total" commutating capacitance at a switching node is (single-device Coss) x (parallel count), and the parallel count is chosen for the current level of the specific design, not a fixed property of the topology. We had been using 2025's own parallel count (1 high-side, 2 low-side GS61008T), sized for its ~50 A phase current, without re-deriving it for our 125 A phase current.
- Thank you for the flying-capacitor part number, Murata GRM32EC72A106KE05L (10 uF, +-10%, 100 V, X7S, 1210 case). Two things we're still unsure about and would like to confirm when convenient: (1) is this the nominal value, or already corrected for DC-bias derating (X7S dielectrics lose significant capacitance under bias, and C1/C2/C3 sit at different bias points in the ladder, so their effective values may differ even as the same part), and (2) is this 2025's actual hardware part, or a value you're giving specifically for the 2024 case?
- You mentioned it's possible the 2025 lab's inductor/capacitor choices were constrained by what their supplier had in stock at the time, rather than a value derived purely from the design equations - you weren't certain of this yourself. If true, it's a further reason not to treat 2025's component values as portable design targets even for its own operating point, let alone ours.

## What we did afterward

We found that 2024's own Table 3 (the embedded/3-D-package section) names a specific device for our exact nP=4, nM=4 configuration: 2 parallel EPC2067 on the high side, 3 parallel EPC2067 on the low side. This is a paper-native candidate, as opposed to the GS61008T we'd been borrowing from 2025. We looked up EPC2067's real datasheet Coss (Co(tr)=1860 pF/device) and reran our full local commutation chain (interval 1 through interval 3, since the larger low-side capacitance also changes the interval-2 handoff state, not just the final ZVS step) with this candidate, keeping every other quantity - Vin, Vo, nP, nM, Ipk, L, Ton - identical to our existing GS61008T-based run.

Result: the local natural-ZVS threshold moves from 7.76%-7.77% (GS61008T assumption) to 22.04%-22.05% (EPC2067 assumption) - about 2.8x higher. The direction is physically correct: a larger commutation capacitance needs more charge to swing the same voltage.

We then combined this with two earlier sensitivity sweeps that share the same base circuit (a snubber-capacitance sweep and a Coss-scale sweep) into one dataset - 102 points spanning about a 9x range in effective commutation capacitance - and fit a simple model: the minimum achieved Vds falls off as roughly 1/sqrt(C_eff), with the exponent coming out to 0.51 +/- 0.01 from the fit itself (not assumed), R^2 ~ 0.95. That's a fairly strong indication the underlying resonant-commutation mechanism is correctly modeled, largely independent of which specific device number goes into it.

Inverting that fit gives a specific number worth flagging: to reach natural ZVS at literally 1%-2% negative current (as 2024 states), the effective commutation capacitance would need to be only about 4-17 pF - one to two orders of magnitude smaller than either GS61008T's (~257 pF) or EPC2067's (~2232 pF) effective value. That gap is large enough that we don't think it's explained by picking a different realistically-sized device. Our best guesses are (a) the real nonlinear Coss(V) curve near Vds->0 makes the last part of the swing effectively "free" in a way our constant-capacitance approximation doesn't capture, or (b) the real dead-time budget is longer than our 50 ns observation window allows, giving a partial resonant swing more time to complete. We don't have a way to distinguish these without real numbers.

Separately, we noticed two 2026 papers in the same author line (yourself, Ramin Rahimzadeh Khorasani, and the broader consortium): "A Comprehensive Design Framework for Vertical Power Delivery in HPC" and "Integrated Vertical Power Delivery - Review & Challenges." Together with 2025's paper explicitly being a real, measured 12V/200W/3-phase prototype (versus 2024's 48V/1kW/4-phase case, which reads throughout as an analytical/optimization target rather than a built and measured one - Section IV even calls the embedded-package version "conceptual" and "future work"), this makes us suspect the 48V/1kW/4-phase configuration itself may never have been physically built or measured by your group, and that 2025's smaller prototype was the first real hardware validation of the underlying ZVS mechanism. If that's right, it would explain why we can't find a "real" 48V-case device or capacitance number anywhere in the two papers - it may genuinely not exist yet, rather than being something we're failing to extract from the text.

## Three things worth confirming, in order of how much they'd narrow things down

1. Was the 48V/1kW/4-phase case ever built and measured, or is 2025's 12V/200W/3-phase prototype the first (and so far only) real hardware in this line?
2. Is EPC2067 (Table 3) the device you'd associate with the Section II-B ZVS mechanism itself, or is that purely the Section IV embedded-package concept? If the former, is there a validated Rds(on)/Ron figure for it in that context (we currently have no way to model this and left Ron at GS61008T's value as a known limitation)?
3. On the Murata part: nominal or bias-derated, and is it specifically for the 2024 case or 2025's hardware?

Happy to walk through any of the above in more detail whenever convenient. Thank you again for the guidance today - it changed how we're prioritizing the next round of work.

Best,
[name]
