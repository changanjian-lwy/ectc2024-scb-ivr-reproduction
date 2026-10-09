"""A180 (extension lscb_ladder): netlist structure and drive timing; no LTspice needed."""
import re

from scb_ivr.extensions import lscb_ladder as ll


def test_base_has_no_ladder():
    txt = ll.netlist("base", "up1")
    assert not re.search(r"^(CD|DC|SC)\d", txt, re.M)
    assert txt.count("\nSH") == 4 and txt.count("\nSL") == 4 and txt.count("\nCS") == 3


def test_ladder_and_clamp_nodes():
    txt = ll.netlist("d07_c20", "up1")
    for k, (hi, lo) in enumerate((("d1", "0"), ("d2", "d1"), ("d3", "d2"), ("vin", "d3")), 1):
        assert f"\nCD{k} {hi} {lo} " in txt
    for k, d in ((1, "d3"), (2, "d2"), (3, "d1")):                 # anode at the ladder, cathode at a_k
        assert f"\nDC{k} {d} a{k} DCL" in txt
    assert "Vfwd=0.7 " in txt and "\nSC1" not in txt


def test_active_clamp_only_inside_ls_on_and_window():
    p = ll.PARAMS
    gates = ll.gate_intervals("up1")
    txt = ll.netlist("act_c20", "up1")
    for k in (1, 2, 3):
        allowed = [(c, e) for _, _, c, e in gates[k] if c >= p["t_step"] and e <= p["t_step"] + p["t_win"]]
        assert allowed and f"\nSC{k} d{4 - k} a{k} gc{k} 0 SWC" in txt
        assert all(e - c > 0.5 * p["T"] for c, e in allowed)


def test_dead_time_and_order():
    p = ll.PARAMS
    for row in ("up1", "su"):
        for k, iv in ll.gate_intervals(row).items():
            for (a, b, c, e), nxt in zip(iv, iv[1:]):
                assert b < c and c - b >= p["t_dead"] - 1e-15 and e < nxt[0] - p["t_edge"]
                assert nxt[0] - e >= p["t_dead"] - 1e-15


def test_feed_forward_shortens_ton_after_rising_step():
    p = ll.PARAMS
    iv = ll.gate_intervals("up1")[1]
    before = [b - a for a, b, _, _ in iv if a < p["t_step"]]
    after = [b - a for a, b, _, _ in iv if a > p["t_step"] + 2e-6]
    assert abs(before[-1] - p["ton0"]) < 1e-15
    assert abs(after[0] - p["ton0"] * 48 / 52.8) < 1e-15
