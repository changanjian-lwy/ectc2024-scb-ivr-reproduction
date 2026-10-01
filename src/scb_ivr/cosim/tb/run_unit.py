"""Build ../rtl with Icarus Verilog and run the cocotb unit tests (test_scb_ctrl.py); exit code 0 only if all pass.

    python3 src/scb_ivr/cosim/tb/run_unit.py      (the OSS CAD Suite's bin directory is added to PATH)
"""
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from cocotb_tools.runner import get_runner

HERE = Path(__file__).resolve().parent
RTL = HERE.parent / "rtl"
BUILD = HERE.parents[3] / "tmp" / "cosim_unit"
os.environ["PATH"] = f"{Path.home() / 'tools' / 'oss-cad-suite' / 'bin'}:{os.environ.get('PATH', '')}"

runner = get_runner("icarus")
runner.build(sources=[RTL / "sync2.v", RTL / "scb_phase.v", RTL / "scb_ctrl.v"], hdl_toplevel="scb_ctrl",
             parameters={"N": 4, "TW": 32, "FB": 5, "CW": 8}, build_dir=BUILD, always=True)
xml = runner.test(hdl_toplevel="scb_ctrl", test_module="test_scb_ctrl", build_dir=BUILD, test_dir=HERE,
                  results_xml=str(BUILD / "results.xml"))
cases = list(ET.parse(xml).getroot().iter("testcase"))
failed = [c.get("name") for c in cases if c.find("failure") is not None or c.find("error") is not None]
print("ALL PASSED" if not failed else "FAILED:", len(cases), "tests", failed or "")
sys.exit(1 if failed else 0)
