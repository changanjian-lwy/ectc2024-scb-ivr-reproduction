from pathlib import Path


def build(n: int) -> str:
    lines = [
        "* ECTC 2024 topology-scaling experiment",
        f"* Hypothetical {n}-phase, 48 V -> 1 V, 125 W module",
        "* Engineering extension; only the four-phase case is the paper baseline.",
        ".param VIN=48 VOUT_TARGET=1 PMODULE=125 FSW=5Meg",
        f".param NPHASES={n} T={{1/FSW}} D_IDEAL={{NPHASES*VOUT_TARGET/VIN}}",
        ".param D_CMD={1.224*D_IDEAL} TON={D_CMD*T} TDEAD=.2n",
        ".param IPHASE_AVG={PMODULE/(VOUT_TARGET*NPHASES)}",
        ".param LCRIT={VOUT_TARGET*(1-D_IDEAL)/(2*IPHASE_AVG*FSW)}",
        ".param LPHASE={.985*LCRIT} RL_PHASE={13.6m/12}",
        ".param CFLY=12u CFLY_ESR=.5m COUT=100u COUT_ESR=.2m",
        ".param RON_H=7m RON_L=3.5m COSS_H=100p COSS_L=200p",
        ".param RLOAD={VOUT_TARGET*VOUT_TARGET/PMODULE}",
        "VINPUT vin 0 {VIN}",
        "",
        f"* {n} gate pairs, uniformly shifted by T/{n}.",
    ]
    for k in range(1, n + 1):
        shift = "0" if k == 1 else (f"{k-1}*T/{n}" if k > 2 else f"T/{n}")
        q = f"mod(time+T-{shift},T)"
        lines += [
            f"BGH{k} gh{k} 0 V=if({q}>TDEAD/2 & {q}<TON-TDEAD/2,5,0)",
            f"BGL{k} gl{k} 0 V=if({q}>TON+TDEAD/2 & {q}<T-TDEAD/2,5,0)",
        ]
    lines += ["", "* Reusable series-capacitor ladder power stage."]
    previous = "vin"
    for k in range(1, n + 1):
        if k < n:
            next_node = f"a{k}"
            cap_v = (n - k) * 48 / n
            lines += [
                f"SH{k} {previous} {next_node} gh{k} 0 SWH",
                f"C{k} {next_node} sw{k} {{CFLY}} Rser={{CFLY_ESR}} IC={cap_v:g}",
            ]
            previous = next_node
        else:
            lines.append(f"SH{k} {previous} sw{k} gh{k} 0 SWH")
        lines += [
            f"SL{k} sw{k} 0 gl{k} 0 SWL",
            f"L{k} sw{k} l{k}o {{LPHASE}}",
            f"RL{k} l{k}o out {{RL_PHASE}}",
        ]
    lines += ["", "* Reverse-conduction paths and switch capacitances."]
    previous = "vin"
    for k in range(1, n + 1):
        next_node = f"a{k}" if k < n else f"sw{k}"
        lines += [
            f"DH{k} {next_node} {previous} DMOD",
            f"DL{k} 0 sw{k} DMOD",
            f"CH{k} {previous} {next_node} {{COSS_H}}",
            f"CL{k} sw{k} 0 {{COSS_L}}",
        ]
        previous = next_node
    lines += [
        "",
        ".model SWH SW(Ron={RON_H} Roff=100Meg Vt=2.5 Vh=.1)",
        ".model SWL SW(Ron={RON_L} Roff=100Meg Vt=2.5 Vh=.1)",
        ".model DMOD D(Ron=3m Roff=100Meg Vfwd=1.5)",
        "Cout out 0 {COUT} Rser={COUT_ESR}",
        "Rload out 0 {RLOAD}",
        ".ic V(out)=1 " + " ".join(f"I(L{k})=0" for k in range(1, n + 1)),
        ".options reltol=.003",
        ".tran 0 20u 0 .05n UIC",
        ".meas tran VOUT_AVG AVG V(out) FROM 15u TO 20u",
    ]
    for k in range(1, n + 1):
        lines.append(f".meas tran IL{k}_AVG AVG I(L{k}) FROM 15u TO 20u")
    lines += [
        ".meas tran IL1_MAX MAX I(L1) FROM 15u TO 20u",
        ".meas tran IL1_MIN MIN I(L1) FROM 15u TO 20u",
    ]
    for k in range(1, n):
        lines += [
            f".meas tran VC{k}_AVG AVG V(a{k},sw{k}) FROM 15u TO 20u",
            f".meas tran VC{k}_PP PP V(a{k},sw{k}) FROM 15u TO 20u",
        ]
    lines += [
        ".meas tran VDSH1_MIN MIN V(vin,a1) FROM 15u TO 20u" if n > 1 else "",
        ".meas tran OUTPUT_ERROR_PCT PARAM 100*(VOUT_AVG-VOUT_TARGET)/VOUT_TARGET",
        ".meas tran NEGATIVE_CURRENT_PCT PARAM 100*abs(IL1_MIN)/IL1_MAX",
        ".end",
    ]
    return "\n".join(x for x in lines if x != "") + "\n"


root = Path("/Users/lawyer/Desktop/ECTC2024_Teacher_Report/Experiments")
for phases in (2, 3, 6):
    folder = root / f"{phases + 5:02d}_Topology_{phases}Phase"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "model.net").write_text(build(phases))
