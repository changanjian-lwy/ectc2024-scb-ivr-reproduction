from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE / "ectc2024_4phase_4module_sourced_params.net"


def write_variant(name: str, replacements: dict[str, str], insert_after: tuple[str, str] | None = None):
    text = BASE.read_text()
    for old, new in replacements.items():
        if old not in text:
            raise RuntimeError(f"Template text not found: {old}")
        text = text.replace(old, new)
    if insert_after:
        marker, addition = insert_after
        if marker not in text:
            raise RuntimeError(f"Insertion marker not found: {marker}")
        text = text.replace(marker, marker + "\n" + addition)
    (HERE / name).write_text(text)


# E1: Functional current-limited precharge.  It represents the function of
# the two auxiliary MOSFETs in Reusch et al.; it is not yet a device-level
# floating gate-driver implementation.
write_variant(
    "experiment_E1_current_limited_precharge.net",
    {
        "* ECTC 2024 SCB IVR -- sourced-parameter attempt":
            "* E1 -- current-limited flying-capacitor precharge, then 5 MHz PWM",
        ".param TDEAD=2n TENABLE=5u TRAMP=40u":
            ".param TDEAD=2n TENABLE=140u TRAMP=40u\n.param IPRE=10 KPRE=5",
        "VRAIL vin_raw 0 PWL(0 0 {TENABLE} 0 {TENABLE+TRAMP} {VIN} 1m {VIN})":
            "VRAIL vin_raw 0 PWL(0 0 5u 0 {5u+TRAMP} {VIN} 300u {VIN})",
        ".meas tran VOUT_FINAL AVG V(out) FROM 480u TO 500u":
            ".meas tran VOUT_FINAL AVG V(out) FROM 180u TO 200u",
        ".meas tran VC11_FINAL AVG V(xmod1:a1,xmod1:sw1) FROM 480u TO 500u":
            ".meas tran VC11_FINAL AVG V(xmod1:a1,xmod1:sw1) FROM 180u TO 200u",
        ".meas tran VC12_FINAL AVG V(xmod1:a2,xmod1:sw2) FROM 480u TO 500u":
            ".meas tran VC12_FINAL AVG V(xmod1:a2,xmod1:sw2) FROM 180u TO 200u",
        ".meas tran VC13_FINAL AVG V(xmod1:a3,xmod1:sw3) FROM 480u TO 500u":
            ".meas tran VC13_FINAL AVG V(xmod1:a3,xmod1:sw3) FROM 180u TO 200u",
        ".meas tran IL11_MAX MAX I(XMOD1:L1) FROM 450u TO 500u":
            ".meas tran IL11_MAX MAX I(XMOD1:L1) FROM 160u TO 200u",
        ".meas tran IL11_MIN MIN I(XMOD1:L1) FROM 450u TO 500u":
            ".meas tran IL11_MIN MIN I(XMOD1:L1) FROM 160u TO 200u",
        ".meas tran IINPUT_PEAK MAX I(VRAIL) FROM 0 TO 500u":
            ".meas tran IINPUT_PEAK MAX I(VRAIL) FROM 0 TO 200u",
        ".tran 0 500u 0 .5n startup": ".tran 0 200u 0 1n startup",
    },
    (
        "BL4 gl4 g V=if(time>TENABLE & mod(time-MOFF+T-3*T/4,T)>TON+TDEAD/2 & mod(time-MOFF+T-3*T/4,T)<T-TDEAD/2,VGATE,0)",
        "\n* Abstract current-limited auxiliary-FET precharge branches.\n"
        "BPC1 sw1 a1 I=if(time<TENABLE,min(IPRE,max(0,KPRE*(0.75*V(vin,g)-V(a1,sw1)))),0)\n"
        "BPC2 sw2 a2 I=if(time<TENABLE,min(IPRE,max(0,KPRE*(0.50*V(vin,g)-V(a2,sw2)))),0)\n"
        "BPC3 sw3 a3 I=if(time<TENABLE,min(IPRE,max(0,KPRE*(0.25*V(vin,g)-V(a3,sw3)))),0)",
    ),
)


# E2: Slow-ramp, low-frequency natural-balancing screen.  Frequency and
# inductance are scaled together to preserve the Table-1 boundary relation.
write_variant(
    "experiment_E2_slow_ramp_low_frequency.net",
    {
        "* ECTC 2024 SCB IVR -- sourced-parameter attempt":
            "* E2 -- slow input ramp and low-frequency natural-balancing screen",
        ".param VIN=48 VOUT=1 POUT=1000 NP=4 NM=4 FSW=5Meg T={1/FSW}":
            ".param VIN=48 VOUT=1 POUT=1000 NP=4 NM=4 FSW=100k T={1/FSW}",
        ".param LPHASE=2.68n": ".param LPHASE=134n",
        ".param TDEAD=2n TENABLE=5u TRAMP=40u":
            ".param TDEAD=20n TENABLE=0 TRAMP=10m",
        "VRAIL vin_raw 0 PWL(0 0 {TENABLE} 0 {TENABLE+TRAMP} {VIN} 1m {VIN})":
            "VRAIL vin_raw 0 PWL(0 0 {TRAMP} {VIN} 12m {VIN})",
        ".meas tran VOUT_FINAL AVG V(out) FROM 480u TO 500u":
            ".meas tran VOUT_FINAL AVG V(out) FROM 9.8m TO 10m",
        ".meas tran VC11_FINAL AVG V(xmod1:a1,xmod1:sw1) FROM 480u TO 500u":
            ".meas tran VC11_FINAL AVG V(xmod1:a1,xmod1:sw1) FROM 9.8m TO 10m",
        ".meas tran VC12_FINAL AVG V(xmod1:a2,xmod1:sw2) FROM 480u TO 500u":
            ".meas tran VC12_FINAL AVG V(xmod1:a2,xmod1:sw2) FROM 9.8m TO 10m",
        ".meas tran VC13_FINAL AVG V(xmod1:a3,xmod1:sw3) FROM 480u TO 500u":
            ".meas tran VC13_FINAL AVG V(xmod1:a3,xmod1:sw3) FROM 9.8m TO 10m",
        ".meas tran IL11_MAX MAX I(XMOD1:L1) FROM 450u TO 500u":
            ".meas tran IL11_MAX MAX I(XMOD1:L1) FROM 9.5m TO 10m",
        ".meas tran IL11_MIN MIN I(XMOD1:L1) FROM 450u TO 500u":
            ".meas tran IL11_MIN MIN I(XMOD1:L1) FROM 9.5m TO 10m",
        ".meas tran IINPUT_PEAK MAX I(VRAIL) FROM 0 TO 500u":
            ".meas tran IINPUT_PEAK MAX I(VRAIL) FROM 0 TO 10m",
        ".tran 0 500u 0 .5n startup": ".tran 0 10m 0 20n startup",
    },
)
