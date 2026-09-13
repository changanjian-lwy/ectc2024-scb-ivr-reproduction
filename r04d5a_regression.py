"""Validate P25 Mode-5 device-plug-in commutation."""
from pathlib import Path
import re

LOG = Path(__file__).resolve().parent / "paper_locked/03_apec2025_auxiliary/spice/R04D5A_P25_native_mode5_device_plugin.log"

def _v(t,n,at=False):
    line=re.search(rf"^{n}:(.*)$",t,re.M)
    if not line: raise ValueError(n)
    if at:
        m=re.search(r"\bAT\s+([-+0-9.eE]+)",line.group(1))
        if m:return float(m.group(1))
    return float(re.findall(r"=\s*([-+0-9.eE]+)",line.group(1))[-1])

def validate_existing_result():
    t=LOG.read_text(errors="replace")
    x={"t6":_v(t,"t6_high_vds_zero",True),"il2":_v(t,"il2_at_t6"),
       "vx2":_v(t,"vx2_at_t6"),"ton":_v(t,"t_sh2_gate_on",True),
       "il_on":_v(t,"il2_at_sh2_on")}
    c={"zvs_node":abs(x["vx2"]-4)<1e-6,"negative_at_zvs":x["il2"]<0,
       "gate_after_zero":x["ton"]>=x["t6"],"negative_at_gate":x["il_on"]<0}
    return {"measurements":x,"checks":c,"passed":all(c.values()),
            "claim_boundary":"ideal t5=t4 and GS61008T scalar-capacitance plug-in; no published delay/snubber value"}

if __name__=="__main__":
    r=validate_existing_result();print(r)
    if not r["passed"]:raise SystemExit("R04D5A failed")
