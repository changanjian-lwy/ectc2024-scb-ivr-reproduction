"""Run one A91 co-simulation (copied from A89; RTL: A89's, unchanged): python3 run_cosim.py cfg_<name>.json

Builds rtl/*.v with Icarus Verilog and runs cosim/test_cosim.py, with the configuration passed through
COSIM_CFG. The OSS CAD Suite's bin directory must be on PATH (iverilog, vvp).
"""
import json
import sys
from pathlib import Path

from cocotb_tools.runner import get_runner

HERE = Path(__file__).resolve().parent
RTL = HERE.parent.parent / "A89_verilog_predicted_low_side" / "rtl"   # A91 uses A89's RTL unchanged
cfg_path = (HERE / sys.argv[1]).resolve()
cfg = json.loads(cfg_path.read_text())
build = HERE / f"sim_build_{cfg_path.stem}"

runner = get_runner("icarus")
runner.build(sources=[RTL / "sync2.v", RTL / "scb_phase.v", RTL / "scb_ctrl.v"], hdl_toplevel="scb_ctrl",
             parameters={"N": 4, "TW": 32, "FB": int(cfg["fb"]), "CW": 8}, build_dir=build, always=True)
runner.test(hdl_toplevel="scb_ctrl", test_module="test_cosim", build_dir=build, test_dir=HERE,
            extra_env={"COSIM_CFG": str(cfg_path)})
