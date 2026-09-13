# A02 - previously verified local stages with device Coss

## Locked comparison rule

- P24 remains the sequence/topology source.
- P25 supplies one GS61008T high-side and two parallel GS61008T low-side
  devices; the official datasheet supplies the scalar `Co(tr)` plug-in.
- Device Coss is `385 pF` high-side and `770 pF` low-side.
- External snubber remains zero because P24/P25 omit its numeric value.
- Existing initial states, switching commands, negative-current thresholds and
  stage endpoints are not changed to improve a result.
- Each local result retains its original claim boundary; local success is not
  a complete periodic-orbit or hardware-ZVS claim.

## Experiments

1. A02-1 compares the successful P24 first energy interval with and without
   device Coss. The only electrical change is adding the device capacitances
   with topology-consistent initial voltages.
2. R04D1B2 and R04D2A are re-run as the already established finite Coss
   commutation/freewheel stages.
3. R04D3A (P24 1%), R04D3C (P25 5% mapped branch), and R04D3E (8% calibrated
   model branch) are re-run without changing their threshold branches.
