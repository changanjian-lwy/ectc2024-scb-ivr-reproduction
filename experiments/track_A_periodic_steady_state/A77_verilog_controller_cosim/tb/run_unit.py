"""Build rtl/*.v with Icarus Verilog and run the cocotb unit tests (tb/test_scb_ctrl.py).

The OSS CAD Suite's bin directory must be on PATH (it holds iverilog and vvp); python3 stays the
project's interpreter. Exit code 0 only if every test passes.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from cocotb_tools.runner import get_runner

HERE = Path(__file__).resolve().parent
RTL = HERE.parent / "rtl"
BUILD = HERE / "sim_build"

runner = get_runner("icarus")
runner.build(sources=[RTL / "sync2.v", RTL / "scb_phase.v", RTL / "scb_ctrl.v"], hdl_toplevel="scb_ctrl",
             parameters={"N": 4, "TW": 32, "FB": 5, "CW": 8}, build_dir=BUILD, always=True)
xml = runner.test(hdl_toplevel="scb_ctrl", test_module="test_scb_ctrl", build_dir=BUILD, test_dir=HERE)
cases = ET.parse(xml).getroot().iter("testcase")
failed = [c.get("name") for c in cases if c.find("failure") is not None or c.find("error") is not None]
print("FAILED:" if failed else "ALL PASSED", failed or "")
sys.exit(1 if failed else 0)
