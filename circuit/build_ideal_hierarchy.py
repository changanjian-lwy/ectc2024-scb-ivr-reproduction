from pathlib import Path


HERE = Path(__file__).resolve().parent


def build(module_count: int, inductance: str = "2.68n") -> str:
    power = 250 * module_count
    modules = "\n".join(
        f"XMOD{k + 1} vin out 0 SCB4P PARAMS: MOFF={{({k})*T/(4*NM)}}"
        for k in range(module_count)
    )
    save_caps = " ".join(
        f"V(xmod{k + 1}:a1,xmod{k + 1}:sw1) "
        f"V(xmod{k + 1}:a2,xmod{k + 1}:sw2) "
        f"V(xmod{k + 1}:a3,xmod{k + 1}:sw3)"
        for k in range(module_count)
    )
    save_module_currents = " ".join(
        f"I(XMOD{k + 1}:L1)" for k in range(1, module_count)
    )
    return f"""* I0-{module_count}M -- ideal SCB hierarchy test, zero capacitor initial voltage
* Paper topology/timing only: no precharge, no fixed 36/24/12 V sources, no parasitics.
.param VIN=48 VOUT=1 POUT={power} NP=4 NM={module_count} FSW=5Meg T={{1/FSW}}
.param D={{NP*VOUT/VIN}} TON={{D*T}} RLOAD={{VOUT*VOUT/POUT}}
.param LPHASE={inductance} CFLY=27.34375u COUT=470u
.param RON=1u ROFF=1T RLDAMP=1m VGATE=5 TENABLE=5u

VRAIL vin 0 PWL(0 0 5u 48 60u 48)
{modules}
CCO out 0 {{COUT}}
RLOAD_MAIN out 0 {{RLOAD}}

.meas tran VOUT_AVG AVG V(out) FROM 40u TO 50u
.meas tran VOUT_PP PP V(out) FROM 40u TO 50u
.meas tran VC1_AVG AVG V(xmod1:a1,xmod1:sw1) FROM 40u TO 50u
.meas tran VC2_AVG AVG V(xmod1:a2,xmod1:sw2) FROM 40u TO 50u
.meas tran VC3_AVG AVG V(xmod1:a3,xmod1:sw3) FROM 40u TO 50u
.meas tran VC1_PP PP V(xmod1:a1,xmod1:sw1) FROM 40u TO 50u
.meas tran VC2_PP PP V(xmod1:a2,xmod1:sw2) FROM 40u TO 50u
.meas tran VC3_PP PP V(xmod1:a3,xmod1:sw3) FROM 40u TO 50u
.meas tran IL1_MAX MAX I(XMOD1:L1) FROM 40u TO 50u
.meas tran IL1_MIN MIN I(XMOD1:L1) FROM 40u TO 50u
.meas tran IL1_AVG AVG I(XMOD1:L1) FROM 40u TO 50u
.meas tran IL2_AVG AVG I(XMOD1:L2) FROM 40u TO 50u
.meas tran IL3_AVG AVG I(XMOD1:L3) FROM 40u TO 50u
.meas tran IL4_AVG AVG I(XMOD1:L4) FROM 40u TO 50u
.meas tran ICOUT_AVG AVG I(CCO) FROM 40u TO 50u
.meas tran ILOAD_AVG AVG I(RLOAD_MAIN) FROM 40u TO 50u
.meas tran VL1_AVG AVG V(xmod1:sw1,out) FROM 40u TO 50u
.meas tran VL2_AVG AVG V(xmod1:sw2,out) FROM 40u TO 50u
.meas tran VL3_AVG AVG V(xmod1:sw3,out) FROM 40u TO 50u
.meas tran VL4_AVG AVG V(xmod1:sw4,out) FROM 40u TO 50u
.meas tran IC1_AVG AVG I(XMOD1:CS1) FROM 40u TO 50u
.meas tran IC2_AVG AVG I(XMOD1:CS2) FROM 40u TO 50u
.meas tran IC3_AVG AVG I(XMOD1:CS3) FROM 40u TO 50u
.meas tran IIN_AVG AVG -I(VRAIL) FROM 40u TO 50u
.meas tran PIN_AVG AVG (-V(vin)*I(VRAIL)) FROM 40u TO 50u
.meas tran POUT_AVG AVG (V(out)*V(out)/RLOAD) FROM 40u TO 50u
.meas tran VOUT_40U FIND V(out) AT 40u
.meas tran VOUT_50U FIND V(out) AT 50u

.options plotwinsize=0 reltol=1e-4 abstol=1e-8 chgtol=1e-16
.save V(vin) V(out) V(xmod1:sw4) {save_caps} I(VRAIL) I(CCO) I(RLOAD_MAIN) I(XMOD1:CS1) I(XMOD1:CS2) I(XMOD1:CS3) I(XMOD1:L1) I(XMOD1:L2) I(XMOD1:L3) I(XMOD1:L4) {save_module_currents}
.tran 0 50u 0 .5n startup

.subckt SCB4P vin out g PARAMS: MOFF=0
BH1 gh1 g V=if(time>TENABLE & mod(time-MOFF+T,T)<TON,VGATE,0)
BL1 gl1 g V=if(time>TENABLE & mod(time-MOFF+T,T)>=TON,VGATE,0)
BH2 gh2 g V=if(time>TENABLE & mod(time-MOFF+T-T/4,T)<TON,VGATE,0)
BL2 gl2 g V=if(time>TENABLE & mod(time-MOFF+T-T/4,T)>=TON,VGATE,0)
BH3 gh3 g V=if(time>TENABLE & mod(time-MOFF+T-T/2,T)<TON,VGATE,0)
BL3 gl3 g V=if(time>TENABLE & mod(time-MOFF+T-T/2,T)>=TON,VGATE,0)
BH4 gh4 g V=if(time>TENABLE & mod(time-MOFF+T-3*T/4,T)<TON,VGATE,0)
BL4 gl4 g V=if(time>TENABLE & mod(time-MOFF+T-3*T/4,T)>=TON,VGATE,0)

SH1 vin a1 gh1 g SWI
CS1 a1 sw1 {{CFLY}}
SL1 sw1 g gl1 g SWI
L1 sw1 out {{LPHASE}} Rser={{RLDAMP}}
SH2 a1 a2 gh2 g SWI
CS2 a2 sw2 {{CFLY}}
SL2 sw2 g gl2 g SWI
L2 sw2 out {{LPHASE}} Rser={{RLDAMP}}
SH3 a2 a3 gh3 g SWI
CS3 a3 sw3 {{CFLY}}
SL3 sw3 g gl3 g SWI
L3 sw3 out {{LPHASE}} Rser={{RLDAMP}}
SH4 a3 sw4 gh4 g SWI
SL4 sw4 g gl4 g SWI
L4 sw4 out {{LPHASE}} Rser={{RLDAMP}}

DH1 a1 vin DIDEAL
DL1 g sw1 DIDEAL
DH2 a2 a1 DIDEAL
DL2 g sw2 DIDEAL
DH3 a3 a2 DIDEAL
DL3 g sw3 DIDEAL
DH4 sw4 a3 DIDEAL
DL4 g sw4 DIDEAL
.model SWI SW(Ron={{RON}} Roff={{ROFF}} Vt=2.5 Vh=0)
.model DIDEAL D(Ron={{RON}} Roff={{ROFF}} Vfwd=0)
.ends SCB4P
.end
"""


for count, inductance, name in (
    (1, "2.68n", "experiment_I0A_ideal_1module.net"),
    (4, "2.68n", "experiment_I0B_ideal_4modules.net"),
    (4, "1.467n", "experiment_I0C_ideal_eq4_inductance.net"),
    (4, "1.55n", "experiment_I0G_ideal_near_boundary.net"),
):
    (HERE / name).write_text(build(count, inductance))

# Same ideal one-module circuit; only L is swept.  This isolates the
# Table-I-versus-Eq.-(4) boundary-current question without adding losses.
sweep = build(1, "{LTEST}")
sweep = sweep.replace(
    ".param LPHASE={LTEST} CFLY=27.34375u COUT=470u",
    ".param LPHASE={LTEST} CFLY=27.34375u COUT=470u\n"
    ".step param LTEST list 1.40n 1.467n 1.55n 1.65n 2.00n 2.68n",
)
(HERE / "experiment_I0D_ideal_inductance_sweep.net").write_text(sweep)


def make_long_settle(inductance: str) -> str:
    text = build(4, inductance)
    text = text.replace("FROM 40u TO 50u", "FROM 480u TO 500u")
    text = text.replace("AT 40u", "AT 480u").replace("AT 50u", "AT 500u")
    text = text.replace("VOUT_40U", "VOUT_480U").replace("VOUT_50U", "VOUT_500U")
    text = text.replace("plotwinsize=0", "plotwinsize=500")
    text = text.replace(".tran 0 50u 0 .5n startup", ".tran 0 500u 0 .5n startup")
    return text


(HERE / "experiment_I0E_ideal_table1_long_settle.net").write_text(
    make_long_settle("2.68n")
)
(HERE / "experiment_I0F_ideal_eq4_long_settle.net").write_text(
    make_long_settle("1.467n")
)

# Numerical ideality check: reduce the already-small switch/diode Ron by
# another 1000x.  A materially unchanged result means the remaining offset
# is not ordinary ohmic conduction loss.
ron_check = build(4, "1.55n").replace(".param RON=1u", ".param RON=1n")
(HERE / "experiment_I0H_ideal_ron_check.net").write_text(ron_check)

# Pure lossless limit from zero initial energy.  This is intentionally kept
# separate because an undamped switched LC network need not converge.
lossless = build(4, "1.55n").replace("RLDAMP=1m", "RLDAMP=0")
(HERE / "experiment_I0K_pure_lossless_zero_start.net").write_text(lossless)

# Explicit numerical-damping sweep.  RLDAMP is a regularization variable,
# not an asserted paper component value.
damping_scan = build(1, "1.55n").replace(
    ".param RON=1u ROFF=1T RLDAMP=1m VGATE=5 TENABLE=5u",
    ".param RON=1u ROFF=1T RLDAMP={RDAMP} VGATE=5 TENABLE=5u\n"
    ".step param RDAMP list 1m 0.5m 0.2m 0.1m",
)
(HERE / "experiment_I0L_inductor_damping_sweep.net").write_text(damping_scan)

# Ideal voltage-control layer on top of the explicitly regularized model.
# The 1 mOhm L resistance is kept only as declared startup/numerical damping.
controlled = build(4, "1.55n")
controlled = controlled.replace(
    ".param RON=1u ROFF=1T RLDAMP=1m VGATE=5 TENABLE=5u",
    ".param RON=1u ROFF=1T RLDAMP=1m VGATE=5 TENABLE=5u\n"
    ".param VREF=1 D0={NP*VREF/VIN} KP=0.025 KI=1500 DMIN=0.04 DMAX=0.12",
)
controlled = controlled.replace(
    "VRAIL vin 0 PWL(0 0 5u 48 60u 48)",
    "VRAIL vin 0 PWL(0 0 5u 48 60u 48)\n"
    "BCTRL dctrl 0 V=limit(D0+KP*(VREF-V(out))+KI*idt(VREF-V(out)),DMIN,DMAX)",
)
controlled = controlled.replace(" vin out 0 SCB4P", " vin out 0 dctrl SCB4P")
controlled = controlled.replace(
    ".subckt SCB4P vin out g PARAMS:",
    ".subckt SCB4P vin out g dctrl PARAMS:",
)
controlled = controlled.replace("<TON", "<V(dctrl,g)*T")
controlled = controlled.replace(">=TON", ">=V(dctrl,g)*T")
controlled = controlled.replace(
    ".save V(vin) V(out)", ".save V(vin) V(out) V(dctrl)"
)
controlled = controlled.replace(
    ".meas tran VOUT_AVG", ".meas tran DCTRL_AVG AVG V(dctrl) FROM 40u TO 50u\n"
    ".meas tran VOUT_AVG"
)
(HERE / "experiment_I0M_ideal_voltage_control.net").write_text(controlled)

controlled_long = controlled.replace("FROM 40u TO 50u", "FROM 480u TO 500u")
controlled_long = controlled_long.replace("AT 40u", "AT 480u").replace("AT 50u", "AT 500u")
controlled_long = controlled_long.replace("VOUT_40U", "VOUT_480U").replace("VOUT_50U", "VOUT_500U")
controlled_long = controlled_long.replace("plotwinsize=0", "plotwinsize=500")
controlled_long = controlled_long.replace(".tran 0 50u 0 .5n startup", ".tran 0 500u 0 .5n startup")
(HERE / "experiment_I0N_ideal_voltage_control_long.net").write_text(controlled_long)

controlled_l165_long = controlled_long.replace(".param LPHASE=1.55n", ".param LPHASE=1.65n")
(HERE / "experiment_I0O_ideal_control_L165_long.net").write_text(controlled_l165_long)

# Ideal zero-crossing latch: each low-side gate is set immediately after its
# high-side pulse and reset when its own inductor reaches -INEG.  A tiny state
# capacitor provides ideal memory; it is a controller state, not a power-stage
# parasitic.  This prevents the low side from turning back on after reset.
zc = controlled_long.replace(
    ".param VREF=1 D0={NP*VREF/VIN} KP=0.025 KI=1500 DMIN=0.04 DMAX=0.12",
    ".param VREF=1 D0={NP*VREF/VIN} KP=0.025 KI=1500 DMIN=0.04 DMAX=0.12\n"
    ".param INEG=2 TSET=1n ISET=2m IRESET=2m CSTATE=1p",
)
for k, shift in ((1, "0"), (2, "T/4"), (3, "T/2"), (4, "3*T/4")):
    old = (
        f"BL{k} gl{k} g V=if(time>TENABLE & "
        f"mod(time-MOFF+T-{shift},T)>=V(dctrl,g)*T,VGATE,0)"
        if shift != "0" else
        f"BL{k} gl{k} g V=if(time>TENABLE & "
        f"mod(time-MOFF+T,T)>=V(dctrl,g)*T,VGATE,0)"
    )
    phase_arg = "time-MOFF+T" if shift == "0" else f"time-MOFF+T-{shift}"
    new = (
        f"BSET{k} g st{k} I=if(time>TENABLE & "
        f"mod({phase_arg},T)>=V(dctrl,g)*T & "
        f"mod({phase_arg},T)<V(dctrl,g)*T+TSET,ISET,0)\n"
        f"BRST{k} st{k} g I=if(V(gh{k},g)>2.5 | I(L{k})<-INEG,IRESET,0)\n"
        f"CST{k} st{k} g {{CSTATE}} Rser=0\n"
        f"DHST{k} st{k} one DIDEAL\n"
        f"DLST{k} g st{k} DIDEAL\n"
        f"BGL{k} gl{k} g V=if(V(st{k},g)>.5,VGATE,0)"
    )
    if old not in zc:
        raise RuntimeError(f"Low-side line not found for phase {k}: {old}")
    zc = zc.replace(old, new)
zc = zc.replace(
    ".subckt SCB4P vin out g dctrl PARAMS: MOFF=0",
    ".subckt SCB4P vin out g dctrl PARAMS: MOFF=0\nVONE one g 1",
)
zc = zc.replace(
    ".save V(vin) V(out) V(dctrl)",
    ".save V(vin) V(out) V(dctrl) V(xmod1:gh1) V(xmod1:gl1) V(xmod1:st1)",
)
zc = zc.replace(
    ".meas tran VOUT_AVG",
    ".meas tran GH1_AVG AVG V(xmod1:gh1) FROM 480u TO 500u\n"
    ".meas tran GL1_AVG AVG V(xmod1:gl1) FROM 480u TO 500u\n"
    ".meas tran ST1_MIN MIN V(xmod1:st1) FROM 480u TO 500u\n"
    ".meas tran ST1_MAX MAX V(xmod1:st1) FROM 480u TO 500u\n"
    ".meas tran VOUT_AVG",
)
(HERE / "experiment_I0P_ideal_zero_cross_latch.net").write_text(zc)

# Reduced zero-crossing controller diagnostic: one module and a short run.
# This is used to eliminate threshold chatter before returning to 16 phases.
zc_one = zc.replace(
    ".param VIN=48 VOUT=1 POUT=1000 NP=4 NM=4",
    ".param VIN=48 VOUT=1 POUT=250 NP=4 NM=1",
)
zc_one = "\n".join(
    line for line in zc_one.splitlines()
    if not line.startswith(("XMOD2 ", "XMOD3 ", "XMOD4 "))
)
zc_one = zc_one.replace("FROM 480u TO 500u", "FROM 40u TO 50u")
zc_one = zc_one.replace("AT 480u", "AT 40u").replace("AT 500u", "AT 50u")
zc_one = zc_one.replace("VOUT_480U", "VOUT_40U").replace("VOUT_500U", "VOUT_50U")
zc_one = zc_one.replace(".tran 0 500u 0 .5n startup", ".tran 0 50u 0 .5n startup")
zc_one = zc_one.replace(
    next(line for line in zc_one.splitlines() if line.startswith(".save ")),
    ".save V(vin) V(out) V(dctrl) V(xmod1:sw4) V(xmod1:gh1) V(xmod1:gl1) "
    "V(xmod1:st1) V(xmod1:a1,xmod1:sw1) V(xmod1:a2,xmod1:sw2) "
    "V(xmod1:a3,xmod1:sw3) I(VRAIL) I(CCO) I(RLOAD_MAIN) "
    "I(XMOD1:CS1) I(XMOD1:CS2) I(XMOD1:CS3) I(XMOD1:L1) "
    "I(XMOD1:L2) I(XMOD1:L3) I(XMOD1:L4)",
)
(HERE / "experiment_I0Q_zero_cross_1module_debug.net").write_text(zc_one + "\n")

# Zero-cross controller using the switch model's hysteretic memory instead
# of an analog latch capacitor.  Low side turns on above +10 A after the high
# side turns off, and turns off below -2 A.  It cannot re-trigger near zero.
zc_hyst = controlled_long
for k, shift in ((1, "0"), (2, "T/4"), (3, "T/2"), (4, "3*T/4")):
    old = (
        f"BL{k} gl{k} g V=if(time>TENABLE & "
        f"mod(time-MOFF+T-{shift},T)>=V(dctrl,g)*T,VGATE,0)"
        if shift != "0" else
        f"BL{k} gl{k} g V=if(time>TENABLE & "
        f"mod(time-MOFF+T,T)>=V(dctrl,g)*T,VGATE,0)"
    )
    zc_hyst = zc_hyst.replace(
        old, f"BZC{k} zc{k} g V=if(time<TENABLE,20,if(V(gh{k},g)>2.5,-20,I(L{k})))"
    )
    zc_hyst = zc_hyst.replace(
        f"SL{k} sw{k} g gl{k} g SWI",
        f"SL{k} sw{k} g zc{k} g SWZC on",
    )
zc_hyst = zc_hyst.replace(
    ".model SWI SW(Ron={RON} Roff={ROFF} Vt=2.5 Vh=0)",
    ".model SWI SW(Ron={RON} Roff={ROFF} Vt=2.5 Vh=0)\n"
    ".model SWZC SW(Ron={RON} Roff={ROFF} Vt=4 Vh=6)",
)
zc_hyst = zc_hyst.replace(
    ".subckt SCB4P vin out g dctrl PARAMS: MOFF=0",
    ".subckt SCB4P vin out g dctrl PARAMS: MOFF=0\n"
    "RREG1 a1 g 1Meg\nRREG2 a2 g 1Meg\nRREG3 a3 g 1Meg\n"
    "RREG4 sw1 g 1Meg\nRREG5 sw2 g 1Meg\nRREG6 sw3 g 1Meg\nRREG7 sw4 g 1Meg",
)
zc_hyst = zc_hyst.replace(
    ".options plotwinsize=500 reltol=1e-4",
    ".options plotwinsize=500 reltol=1e-4 gshunt=1e-12",
)
zc_hyst = zc_hyst.replace(
    ".param VIN=48 VOUT=1 POUT=1000 NP=4 NM=4",
    ".param VIN=48 VOUT=1 POUT=250 NP=4 NM=1",
)
zc_hyst = "\n".join(
    line for line in zc_hyst.splitlines()
    if not line.startswith(("XMOD2 ", "XMOD3 ", "XMOD4 "))
)
zc_hyst = zc_hyst.replace("FROM 480u TO 500u", "FROM 40u TO 50u")
zc_hyst = zc_hyst.replace("AT 480u", "AT 40u").replace("AT 500u", "AT 50u")
zc_hyst = zc_hyst.replace("VOUT_480U", "VOUT_40U").replace("VOUT_500U", "VOUT_50U")
zc_hyst = zc_hyst.replace(".tran 0 500u 0 .5n startup", ".tran 0 50u 0 .5n startup")
zc_hyst = zc_hyst.replace(
    next(line for line in zc_hyst.splitlines() if line.startswith(".save ")),
    ".save V(vin) V(out) V(dctrl) V(xmod1:sw4) V(xmod1:gh1) "
    "V(xmod1:zc1) V(xmod1:a1,xmod1:sw1) V(xmod1:a2,xmod1:sw2) "
    "V(xmod1:a3,xmod1:sw3) I(VRAIL) I(CCO) I(RLOAD_MAIN) "
    "I(XMOD1:CS1) I(XMOD1:CS2) I(XMOD1:CS3) I(XMOD1:L1) "
    "I(XMOD1:L2) I(XMOD1:L3) I(XMOD1:L4)",
)
(HERE / "experiment_I0R_zero_cross_hysteresis_1module.net").write_text(zc_hyst + "\n")

# Same hysteretic zero-crossing logic implemented with LTspice's dedicated
# Schmitt A-device; this avoids the hysteretic power-switch initialization
# problem observed in I0R.
zc_schmitt = controlled_long
for k, shift in ((1, "0"), (2, "T/4"), (3, "T/2"), (4, "3*T/4")):
    old = (
        f"BL{k} gl{k} g V=if(time>TENABLE & "
        f"mod(time-MOFF+T-{shift},T)>=V(dctrl,g)*T,VGATE,0)"
        if shift != "0" else
        f"BL{k} gl{k} g V=if(time>TENABLE & "
        f"mod(time-MOFF+T,T)>=V(dctrl,g)*T,VGATE,0)"
    )
    new = (
        f"BZC{k} zc{k} g V=if(time<TENABLE,20,if(V(gh{k},g)>2.5,-20,I(L{k})))\n"
        f"AZC{k} zc{k} g g g g g gl{k} g SCHMITT Vt=4 Vh=6 "
        f"Vhigh={{VGATE}} Vlow=0 Trise=20p Tfall=20p"
    )
    if old not in zc_schmitt:
        raise RuntimeError(f"Complementary low-side line missing in I0S phase {k}")
    zc_schmitt = zc_schmitt.replace(old, new)
zc_schmitt = zc_schmitt.replace(
    ".param VIN=48 VOUT=1 POUT=1000 NP=4 NM=4",
    ".param VIN=48 VOUT=1 POUT=250 NP=4 NM=1",
)
zc_schmitt = "\n".join(
    line for line in zc_schmitt.splitlines()
    if not line.startswith(("XMOD2 ", "XMOD3 ", "XMOD4 "))
)
zc_schmitt = zc_schmitt.replace("FROM 480u TO 500u", "FROM 40u TO 50u")
zc_schmitt = zc_schmitt.replace("AT 480u", "AT 40u").replace("AT 500u", "AT 50u")
zc_schmitt = zc_schmitt.replace("VOUT_480U", "VOUT_40U").replace("VOUT_500U", "VOUT_50U")
zc_schmitt = zc_schmitt.replace(".tran 0 500u 0 .5n startup", ".tran 0 50u 0 .5n startup")
zc_schmitt = zc_schmitt.replace(
    next(line for line in zc_schmitt.splitlines() if line.startswith(".save ")),
    ".save V(vin) V(out) V(dctrl) V(xmod1:sw4) V(xmod1:gh1) "
    "V(xmod1:gl1) V(xmod1:zc1) V(xmod1:a1,xmod1:sw1) "
    "V(xmod1:a2,xmod1:sw2) V(xmod1:a3,xmod1:sw3) I(VRAIL) "
    "I(CCO) I(RLOAD_MAIN) I(XMOD1:CS1) I(XMOD1:CS2) I(XMOD1:CS3) "
    "I(XMOD1:L1) I(XMOD1:L2) I(XMOD1:L3) I(XMOD1:L4)",
)
(HERE / "experiment_I0S_zero_cross_schmitt_1module.net").write_text(zc_schmitt + "\n")

# Homotopy to the lossless periodic state: use declared damping only during
# natural startup, then bypass it after the capacitor ladder has converged.
lossless_homotopy = controlled_long.replace(".param LPHASE=1.55n", ".param LPHASE=1.467n")
lossless_homotopy = lossless_homotopy.replace(
    "BCTRL dctrl 0 V=limit(D0+KP*(VREF-V(out))+KI*idt(VREF-V(out)),DMIN,DMAX)",
    "BCTRL dctrl 0 V=limit(D0+KP*(VREF-V(out))+KI*idt(VREF-V(out)),DMIN,DMAX)\n"
    "VBYP gbyp 0 PWL(0 0 200u 0 220u 5 500u 5)",
)
lossless_homotopy = lossless_homotopy.replace(" vin out 0 dctrl SCB4P", " vin out 0 dctrl gbyp SCB4P")
lossless_homotopy = lossless_homotopy.replace(
    ".subckt SCB4P vin out g dctrl PARAMS:",
    ".subckt SCB4P vin out g dctrl gbyp PARAMS:",
)
for k in range(1, 5):
    lossless_homotopy = lossless_homotopy.replace(
        f"L{k} sw{k} out {{LPHASE}} Rser={{RLDAMP}}",
        f"L{k} sw{k} ld{k} {{LPHASE}} Rser=0\n"
        f"RDAMP{k} ld{k} out {{RLDAMP}}\n"
        f"SBYP{k} ld{k} out gbyp g SWBYP",
    )
lossless_homotopy = lossless_homotopy.replace(
    ".model SWI SW(Ron={RON} Roff={ROFF} Vt=2.5 Vh=0)",
    ".model SWI SW(Ron={RON} Roff={ROFF} Vt=2.5 Vh=0)\n"
    ".model SWBYP SW(Ron=1n Roff=1T Vt=2.5 Vh=0)",
)
lossless_homotopy = lossless_homotopy.replace(
    ".save V(vin) V(out) V(dctrl)",
    ".save V(vin) V(out) V(dctrl) V(gbyp)",
)
(HERE / "experiment_I0T_lossless_after_balanced_startup.net").write_text(lossless_homotopy)

# Hysteretic zero-crossing takes over only after the conventional damped
# startup has established the capacitor ladder.  This gives every hysteretic
# element a definite initial OFF state and avoids floating startup modes.
zc_takeover = lossless_homotopy
for k, shift in ((1, "0"), (2, "T/4"), (3, "T/2"), (4, "3*T/4")):
    old_bl = (
        f"BL{k} gl{k} g V=if(time>TENABLE & "
        f"mod(time-MOFF+T-{shift},T)>=V(dctrl,g)*T,VGATE,0)"
        if shift != "0" else
        f"BL{k} gl{k} g V=if(time>TENABLE & "
        f"mod(time-MOFF+T,T)>=V(dctrl,g)*T,VGATE,0)"
    )
    new_bl = old_bl.replace("time>TENABLE &", "time>TENABLE & time<240u &")
    zc_takeover = zc_takeover.replace(old_bl, new_bl)
    old_sl = f"SL{k} sw{k} g gl{k} g SWI"
    new_sl = (
        old_sl + "\n" +
        f"BZC{k} zc{k} g V=if(time<220u,-20,if(V(gh{k},g)>2.5,-20,I(L{k})))\n" +
        f"SLZC{k} sw{k} g zc{k} g SWZC off"
    )
    zc_takeover = zc_takeover.replace(old_sl, new_sl)
zc_takeover = zc_takeover.replace(
    ".model SWBYP SW(Ron=1n Roff=1T Vt=2.5 Vh=0)",
    ".model SWBYP SW(Ron=1n Roff=1T Vt=2.5 Vh=0)\n"
    ".model SWZC SW(Ron={RON} Roff={ROFF} Vt=4 Vh=6)",
)
zc_takeover = zc_takeover.replace(
    ".save V(vin) V(out) V(dctrl) V(gbyp)",
    ".save V(vin) V(out) V(dctrl) V(gbyp) V(xmod1:gh1) "
    "V(xmod1:gl1) V(xmod1:zc1)",
)
(HERE / "experiment_I0U_zero_cross_takeover_full.net").write_text(zc_takeover)

# Practical numerical realization of the same ideal zero-current rule.  The
# comparator observes a 100 ps delayed current, representing controller
# propagation only (not a power-stage parasitic).  This breaks the algebraic
# loop that made I0U chatter at the exact switching threshold.  The low-side
# switch still turns off at the first detected -2 A crossing, so its off-time
# varies independently in every phase and cycle.
zc_takeover_delayed = zc_takeover
for k in range(1, 5):
    zc_takeover_delayed = zc_takeover_delayed.replace(
        f"if(V(gh{k},g)>2.5,-20,I(L{k})))",
        f"if(V(gh{k},g)>2.5,-20,delay(I(L{k}),100p)))",
    )
zc_takeover_delayed = zc_takeover_delayed.replace(
    ".param INEG=2", ".param INEG=2 TCTRL=100p"
) if ".param INEG=2" in zc_takeover_delayed else zc_takeover_delayed
(HERE / "experiment_I0V_zero_cross_delayed_takeover_full.net").write_text(
    zc_takeover_delayed
)

# First clean variable-off-time experiment.  Keep the already validated
# 1 mOhm numerical/startup damping and change only the low-side turn-off
# instant.  ZEND is the normalized cycle position at which the low side is
# opened; unlike complementary PWM it can leave a genuine all-switches-off
# interval before the next high-side pulse.  Separate files keep each run and
# its changed variable auditable.
for zend, tag in ((0.96, "096"), (0.98, "098"), (0.99, "099"), (1.00, "100")):
    vot = controlled_long.replace(
        ".param VREF=1 D0={NP*VREF/VIN} KP=0.025 KI=1500 DMIN=0.04 DMAX=0.12",
        ".param VREF=1 D0={NP*VREF/VIN} KP=0.025 KI=1500 DMIN=0.04 DMAX=0.12\n"
        f".param ZEND={zend}",
    )
    for k, shift in ((1, "0"), (2, "T/4"), (3, "T/2"), (4, "3*T/4")):
        phase_arg = "time-MOFF+T" if shift == "0" else f"time-MOFF+T-{shift}"
        old = (
            f"BL{k} gl{k} g V=if(time>TENABLE & "
            f"mod({phase_arg},T)>=V(dctrl,g)*T,VGATE,0)"
        )
        new = (
            f"BL{k} gl{k} g V=if(time>TENABLE & "
            f"mod({phase_arg},T)>=V(dctrl,g)*T & "
            f"mod({phase_arg},T)<ZEND*T,VGATE,0)"
        )
        if old not in vot:
            raise RuntimeError(f"Complementary low-side line missing in I0W phase {k}")
        vot = vot.replace(old, new)
    (HERE / f"experiment_I0W_variable_offtime_Z{tag}.net").write_text(vot)

# Ideal fixed-frequency on-time scan.  This does not assert that a changed
# duty is the paper value; it identifies the control action required to move
# the simulated operating point from about 0.94 V to 1 V.
duty_scan = build(1, "1.55n")
duty_scan = duty_scan.replace(
    ".param D={NP*VOUT/VIN} TON={D*T} RLOAD={VOUT*VOUT/POUT}",
    ".param D={DSCAN} TON={D*T} RLOAD={VOUT*VOUT/POUT}\n"
    ".step param DSCAN list 0.0833333 0.085 0.087 0.089 0.091 0.093",
)
(HERE / "experiment_I0I_ideal_on_time_sweep.net").write_text(duty_scan)

# Fine ideal calibration near 1 V: duty and L are the only two variables.
fine_scan = build(1, "{LTEST}")
fine_scan = fine_scan.replace(
    ".param D={NP*VOUT/VIN} TON={D*T} RLOAD={VOUT*VOUT/POUT}",
    ".param D={DSCAN} TON={D*T} RLOAD={VOUT*VOUT/POUT}\n"
    ".step param DSCAN list 0.088 0.0885 0.089\n"
    ".step param LTEST list 1.58n 1.60n 1.62n",
)
(HERE / "experiment_I0J_ideal_duty_inductance_fine_sweep.net").write_text(fine_scan)
