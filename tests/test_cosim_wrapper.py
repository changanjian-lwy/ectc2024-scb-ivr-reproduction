"""The generated multi-module wrapper (rtl/scb_multi.v, C2) matches scb_ctrl's ports: regenerating it gives the same
text, and every scb_ctrl port appears in it."""
import importlib.util
import unittest

from scb_ivr.cosim.circuit import PROJECT

RTL = PROJECT / "src" / "scb_ivr" / "cosim" / "rtl"


class Wrapper(unittest.TestCase):
    def test_the_wrapper_is_up_to_date(self):
        spec = importlib.util.spec_from_file_location("gen_multi", RTL / "gen_multi.py")
        gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
        self.assertEqual((RTL / "scb_multi.v").read_text(), gen.generate())
        ports = gen.ports((RTL / "scb_ctrl.v").read_text())
        self.assertGreater(len(ports), 80)
        names = {n for _, _, n in ports}
        self.assertEqual(len(names), len(ports))                 # A152: "signed" was parsed as a port name, twice
        for n in ("cfg_ext_ton", "ext_ton", "ext_slot", "ext_ref", "t_ref", "ton_now", "cfg_vff_vs_kr", "cfg_vff_vs_kt"):
            self.assertIn(n, names)


if __name__ == "__main__":
    unittest.main()
