"""Lock the P25 Mode-6 physical/equation mismatch."""
from pathlib import Path
import re

LOG = Path(__file__).resolve().parent / "paper_locked/03_apec2025_auxiliary/spice/R04D6A_P25_native_mode6_physical_circuit.log"

def _v(t,n):
    line=re.search(rf"^{n}:(.*)$",t,re.M)
    if not line:raise ValueError(n)
    return float(re.findall(r"=\s*([-+0-9.eE]+)",line.group(1))[-1])

def validate_existing_result():
    t=LOG.read_text(errors="replace")
    x={n:_v(t,n) for n in ("il2_end_physical","ton_used","duty_used","vl2_initial",
                            "eq15_delta_i","eq16_peak_from_t6","p24_eq2_reference_peak")}
    c={"paper_duty":abs(x["duty_used"]-.25)<1e-12,"paper_ton":abs(x["ton_used"]-500e-9)<1e-15,
       "physical_voltage_is_three_v":abs(x["vl2_initial"]-3)<.05,
       "physical_rise_occurs":x["il2_end_physical"]>0,
       "printed_eq15_differs_from_circuit":abs(x["eq16_peak_from_t6"]-x["il2_end_physical"])>20,
       "peak_constraints_not_closed":abs(x["p24_eq2_reference_peak"]-x["il2_end_physical"])>10}
    return {"measurements":x,"checks":c,"passed":all(c.values()),
            "claim_boundary":"Mode-6 qualitative rise succeeds; quantitative peak reproduction is blocked by non-closing published constraints"}

if __name__=="__main__":
    r=validate_existing_result();print(r)
    if not r["passed"]:raise SystemExit("R04D6A regression changed")
