# Step 03 - Auxiliary module scan

## Framework rule

The framework keeps three fixed slots:

1. `commutation_parameters`
2. `boundary_controller`
3. `startup_strategy`

The primary 2024/2025 record inside each slot remains unchanged and unresolved
where the papers omit implementation data. Material from another paper is
registered as a separate candidate with its own source, topology and
compatibility. Registering a candidate does not make it part of the 2024
reproduction.

The executable registry is `framework_modules.py`.

## Slot 1 - commutation parameters

### Primary SCB record

The 2025 paper provides the commutation mechanism and Eqs. (5)-(6) and
(13)-(14), but it does not report numerical CH/CL values or a numerical dead
time. The capacitor part numbers in Table III are incomplete family strings,
not full orderable suffixes.

### Candidate found in the folder

Source: *Hybrid Switched-Capacitor Power Converters: Fundamental Limits and
Design Techniques*, Chapter 6, Eqs. (6.1)-(6.5), PDF pp. 141-142.

Transcribed relations:

`L*Ioff^2 > Coss,total*Vswitch^2`

`L*Ineg^2 > Coss,total*Vswitch^2`

`Coss,Qeq(VDS) = Qoss(VDS)/VDS = integral(Coss(v)dv, 0..VDS)/VDS`

`Imin = sqrt(Coss,total*Vswitch^2/L)`

`tdead,min = (pi/2)*sqrt(L*Coss,total)` under the source paper's assumptions.

The example uses `L=180 nH`, `Coss,total=1.5 nF`, and compares 26 ns, 36 ns
and 46 ns dead times. These numbers belong to a cascaded resonant converter
and are not copied into the SCB parameter set.

Compatibility: `GENERAL_PHYSICS_ONLY`. The charge-equivalent Coss treatment
and energy boundary may be reused after deriving the actual SCB commutation
network. The example values and quarter-cycle formula may not be inserted
without that derivation.

## Slot 2 - boundary controller

No directly reusable implementation was found in the local PDFs.

The 2025 paper states that sensing one inductor current per module is
sufficient, recommends a high-frequency zero-cross detector such as its
reference [22], and lists adjustable on/off-time or constant-off-time control.
However, reference [22] itself is not present in the folder and the paper does
not report detector threshold, blanking, propagation delay or logic.

The three-level startup paper contains current-mode capacitor-balancing
control, but it does not implement the SCB boundary-mode ZCD. It is therefore
not registered as a boundary-controller candidate.

Compatibility: primary slot remains `UNRESOLVED`.

## Slot 3 - startup strategy

### Candidate found in the folder

Source: David Reusch, *Three Level Buck Converter with Control and Soft
Startup*, Section III-C and Fig. 8, PDF pp. 4-5.

Transcribed operating method:

1. Place two small external MOSFETs in series with the flying capacitor.
2. Slowly ramp their gate voltages so that the devices operate in saturation
   as voltage-controlled current sources and limit charging current.
3. Use a resistive divider to set the flying-capacitor target to `0.5*Vin`.
4. When the target is reached, a comparator changes state and turns the
   startup devices off.
5. The paper's Saber example reaches about 7 A peak charging current; a slower
   ramp reduces current at the cost of longer startup time.

Compatibility: `ADAPTATION_REQUIRED`. The source circuit is a three-level buck
with one flying capacitor. Before it can enter the four-phase SCB model, the
targets and safe charge paths for C1-C3 must be derived and the extra paths
must be shown not to disturb the normal SCB modes. The 7 A result is retained
only as source evidence, not as a project parameter.

## Current gate result

- Fixed slot interfaces: complete.
- Candidate registry: complete for the PDFs currently in the folder.
- Direct SCB commutation implementation: unresolved.
- Direct SCB ZCD/controller: unresolved.
- Direct SCB startup implementation: unresolved.
- Publication-locked SPICE: still blocked.

