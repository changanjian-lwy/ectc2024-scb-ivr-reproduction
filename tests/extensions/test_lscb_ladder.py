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


def _pwl_points(txt, name):
    """(t, v) points of PWL source V<name> in a netlist."""
    lines = txt.split("\n")
    i = next(j for j, ln in enumerate(lines) if ln.startswith(f"V{name} "))
    body = []
    for ln in lines[i + 1:]:
        if not ln.startswith("+ "):
            break
        body += ln[2:].rstrip(")").split()
    vals = [float(x) for x in body]
    return list(zip(vals[0::2], vals[1::2]))


def test_detector_window_overlaps_ls_intervals():
    """A182: p["win"] closes the switch on the overlap of each LS on-interval with the window, mid-interval allowed."""
    p = ll.PARAMS
    gates = ll.gate_intervals("up1")
    w0, w1 = p["t_step"] + 0.37e-6, p["t_step"] + 3.0e-6
    txt = ll.netlist("act_c20", "up1", {"win": (w0, w1)})
    for k in (1, 2, 3):
        pts = _pwl_points(txt, f"gc{k}")
        rises = [t for (t, v), (t2, v2) in zip(pts, pts[1:]) if v == 0 and v2 == 1]
        expect = [max(c, w0) for _, _, c, e in gates[k] if e > w0 + p["t_edge"] and c < w1 - p["t_edge"]]
        assert rises == [float(f"{x:.9g}") for x in expect]
        assert rises[0] >= w0 and pts[-1][0] <= w1 + p["t_edge"] + 1e-15


def test_default_netlist_unchanged_by_new_options():
    assert ll.netlist("act_c20", "up1") == ll.netlist("act_c20", "up1", {"win": None, "save_ls": False})
    assert "I(SL1)" in ll.netlist("base", "up1", {"save_ls": True}) and "I(SL1)" not in ll.netlist("base", "up1")


def test_detect_first_crossing_and_pre_max():
    import numpy as np
    t = np.linspace(0.0, 10e-6, 1001)
    names = ["time", "V(d3)", "V(a1)", "V(x1)", "V(d2)", "V(a2)", "V(x2)", "V(d1)", "V(a3)", "V(x3)"]
    dev1 = np.where(t < 5e-6, 0.2 * np.sin(t * 2e6), (t - 5e-6) * 1e6)          # ramps 1 V/us after 5 us
    cols = [t, 36.0 + 0 * t, 36.0 - dev1, 0 * t, 24.0 + 0 * t, 24.0 + 0 * t, 0 * t, 12.0 + 0 * t, 12.0 + 0 * t, 0 * t]
    arr = np.stack(cols, axis=1)
    t_hit, pre = ll.detect(names, arr, 0.75, 5e-6)
    assert abs(t_hit - 5.75e-6) < 1.1e-8 and 0.19 < pre <= 0.2
    assert ll.detect(names, arr, 9.0, 5e-6)[0] is None
