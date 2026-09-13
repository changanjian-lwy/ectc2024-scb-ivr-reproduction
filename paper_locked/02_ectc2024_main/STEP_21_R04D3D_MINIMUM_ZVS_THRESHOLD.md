# Step 21 - R04D3D minimum ZVS threshold search

## Search boundary

The R04D3C topology, initial state and component values were frozen.  Only the
negative-current fraction was changed.  The success event is the first
observed `Vds(QH1)=0` crossing; no waveform was tuned for appearance.

## Results

- Coarse scan 5%-12%: 7% failed; 8% succeeded.
- Fine scan 7.1%-8.0%: 7.7% failed; 7.8% succeeded.
- Refined scan in 0.01 percentage-point increments:
  - 7.76%, `Ineg=-9.700 A`: failed; minimum high-side Vds = 13.924 mV.
  - 7.77%, `Ineg=-9.7125 A`: first zero crossing at 16.6469 ns.

The current model's minimum observed ZVS threshold is therefore 7.77%.
It is stored as `MODEL_CALIBRATION`, not as a P24 or P25 value.

## Library policy

- P24 source values 1% and 2% remain available.
- P25 source values 5% and 10% remain available.
- The exact current R04D3 model defaults to 7.77%.
- Any change to inductance, voltage, switch population/Coss view, topology or
  initial state invalidates automatic reuse and requires recalibration.
