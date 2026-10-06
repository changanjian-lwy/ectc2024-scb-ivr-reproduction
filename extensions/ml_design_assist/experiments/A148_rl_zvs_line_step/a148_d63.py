"""A148: D63 (with the turn-on V_DS block) under the frozen controller's phase-1 Ton cap (scb_vff.v: A128 gate, A136
relative cap on ton's low-pass, RTL integers) and an offset on phase 1's timed low-side edge (lo_add).

Laws for the offset (physics baselines):
- "vs": volt-second balance of phase 1's inductor. The valley stays put when (V_rail1 - Vo) Ton1 = Vo dlo, so the
  edge moves by g ((rail - Vo) Ton1 - (rss - Vo) tlp) / Vo, with scb_vff's own estimates: rail - Vo = Vin's linear
  prediction - 3/4 of its slow low-pass - Vo, rss - Vo the same from the slow low-pass, tlp ton's slow low-pass,
  Ton1 the phase-1 Ton of this period (after the cap). Zero in steady state up to Ton's dither.
- "vs_rail": only the rail term g tlp ((rail - Vo) - (rss - Vo)) / Vo, exactly zero at constant Vin.
- "none": the frozen design (smax 64); the design's smax can be raised separately.
"""
from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path

import numpy as np

from scb_ivr.extensions import ml_rl_ff as FF
from scb_ivr.p24_valley_map import DIVERGED_A, ValleyMap, steady_ton

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent / "A126_ppo_line_feedforward" / "a126_design.json"
VFF = {"c": [64, -47, -47, -139], "k": 844800, "sh2": 2, "sh20": 6, "vin_lsb_v": 0.02, "gth": 100}
REL = 320
LSB = 4e-9 / 128
VO = 1.0
T_STEP = 20e-6
ROWS = {"n0": ("none",), **{k[5:]: v for k, v in FF.A124_ROWS.items()}}
V_SS = 3.9                      # phase 1's steady turn-on V_DS (cosim 3.9 V, D63 3.95 V)
V_HARD = 6.0                    # a turn-on counts as hard above this


def table_path(m=1.0):
    return HERE / ("a148_von_table.json" if m == 1.0 else f"a148_von_table_m{round(m * 100):03d}.json")


def design(smax=64, cs=6e-6, m=1.0):
    """A124's design at L x m (A132's d63_design scaling: t_tr x sqrt(m), I_th / sqrt(m)) with its V_DS table."""
    t = json.loads(table_path(m).read_text())
    d = FF.design(DESIGN, cs)
    if m != 1.0:
        r, t13, t4 = d.ith
        d = replace(d, lf=d.lf * m, t_tr=tuple(x * math.sqrt(m) for x in d.t_tr),
                    ith=(r, tuple(x / math.sqrt(m) for x in t13), tuple(x / math.sqrt(m) for x in t4)))
    return replace(d, smax=smax, von=(tuple(t["currents"]), tuple(t["rails"]), tuple(map(tuple, t["v13"])),
                                      tuple(map(tuple, t["v4"]))))


class Vff:
    """scb_vff.v per Vin sample (phase 1's turn-on), RTL integers (A135 VffRTL + A136 VffLP): (scale, cap) for the
    next period; keeps rail, rss (Q8 codes of vin_lsb, minus Vo) and tlp (Q8 LSB) for the offset laws."""

    def __init__(self, rel=REL):
        self.rel, self.s, self.tlp = rel, None, None
        self.rail = self.rss = 0

    def __call__(self, vin, ton_s):
        t8 = round(ton_s / LSB) << 8
        self.tlp = t8 if self.tlp is None else self.tlp + ((t8 - self.tlp) >> VFF["sh20"])
        ton = self.tlp >> 8
        v = round(vin / VFF["vin_lsb_v"])
        v8, vo8 = v << 8, round(VO / VFF["vin_lsb_v"]) << 8
        s = self.s
        if s is None:
            lp2n = lp20n = vpred = v8
            s = self.s = {"gate": False, "cap": None}
        else:
            lp2n = s["lp2"] + ((v8 - s["lp2"]) >> VFF["sh2"])
            lp20n = s["lp20"] + ((v8 - s["lp20"]) >> VFF["sh20"])
            vpred = 2 * v8 - (s["vprev"] << 8)
        gn = max(lp2n - v8, 0)
        gate = True if gn >= VFF["gth"] << 8 else (False if gn == 0 else s["gate"])
        rail = vpred - ((lp20n * 3) >> 2) - vo8
        rss = lp20n - ((lp20n * 3) >> 2) - vo8
        cap_prev = s["cap"]
        s["cap"] = min(ton * ((rss * self.rel) >> 8), 2 ** 32 - 1) // rail if rail > 0 and rss > 0 else None
        s.update(lp2=lp2n, lp20=lp20n, vprev=v, gate=gate)
        self.rail, self.rss = rail, rss
        g = gn if gate else 0
        scale = [1 + max(min(c * g, 1 << 22), -(1 << 23)) / 2 ** 24 for c in VFF["c"]]
        return scale, [cap_prev * LSB if cap_prev is not None else math.inf] + [math.inf] * 3

    def volts(self, q8):
        return q8 / 256 * VFF["vin_lsb_v"]


def law(name, g=1.0):
    """lo_add factory: f(vff, prev record) -> lo_add for this period (a function of Ton1, or None)."""
    if name == "none":
        return lambda vff, prev=None: None
    if name == "vs":
        return lambda vff, prev=None: (lambda ton1: g * (ton1 * vff.volts(vff.rail) - (vff.tlp >> 8) * LSB * vff.volts(vff.rss)) / VO)
    if name == "vs_rail":
        return lambda vff, prev=None: g * (vff.tlp >> 8) * LSB * (vff.volts(vff.rail) - vff.volts(vff.rss)) / VO
    raise ValueError(name)


def stim(row, t):
    st = ROWS[row]
    vin, i_step = 48.0, 0.0
    if st[0] == "line":
        vin += st[1] * min(max((t - T_STEP) / (st[2] * 1e-6), 0.0), 1.0)
    elif st[0] == "load" and t >= T_STEP:
        i_step = st[1]
    return vin, i_step


def warm(d):
    """A135's warm-up: 600 comparator periods, then 200 timed, with the cap. Returns (map, state, vff, ton)."""
    vff = Vff()
    mw = ValleyMap(replace(d, mode="cmp"))
    s = mw.init_state(steady_ton(d))
    ton = s["acc"]
    for _ in range(600):
        sc, cap = vff(d.vin, ton)
        ton = mw.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    vm = ValleyMap(d)
    for _ in range(200):
        sc, cap = vff(d.vin, ton)
        ton = vm.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    s["t"] = 0.0
    return vm, s, vff, ton


def run(d, row, lo_law, n=1000, state=None):
    """One row from the warm state; lo_law(vff, rec_prev) -> lo_add. Returns the records (with vin, lo_add)."""
    vm, s, vff, ton = state or warm(d)
    recs, prev = [], None
    while len(recs) < n:
        vin, i_step = stim(row, s["t"])
        sc, cap = vff(vin, ton)
        add = lo_law(vff, prev)
        r = vm.period(s, vin, i_step, ton_scale=sc, ton_cap=cap, lo_add=add)
        ton = r["ton"]
        r["vin"], r["lo_add"] = vin, (add(r["tons"][0]) if callable(add) else (add or 0.0))
        recs.append(r)
        prev = r
        if not all(math.isfinite(x) and abs(x) < DIVERGED_A for x in r["valley"] + r["peak"]):
            r["diverged"] = True
            break
    return recs


def stats(recs, d=None, t_step=T_STEP):
    """Per run, after the step: phase 1's turn-on V_DS (max, hard periods, excess V x periods over V_SS), every
    phase's max V_DS, peak, Vo extreme and last exit from 1 %, valley ranges, late fires, the largest offset."""
    a = [r for r in recs if r["t"] >= t_step]
    von1 = np.array([r["von"][0] for r in a])
    vo = np.array([r["vo"] for r in a])
    t = np.array([r["t"] for r in a])
    bad = np.nonzero(np.abs(vo - VO) > 0.01)[0]
    return {"von1_max": float(von1.max()), "von1_hard": int((von1 > V_HARD).sum()),
            "von1_excess": float(np.clip(von1 - V_SS, 0, None).sum()),
            "von_max": [float(max(r["von"][k] for r in a)) for k in range(4)],
            "peak_max": float(max(max(r["peak"]) for r in a)), "extreme_mv": float(1e3 * (vo[np.argmax(np.abs(vo - VO))] - VO)),
            "back_us": float((t[bad[-1]] - t_step) * 1e6) if len(bad) else 0.0,
            "valley_min": [float(min(r["valley"][k] for r in a)) for k in range(4)],
            "valley_max": [float(max(r["valley"][k] for r in a)) for k in range(4)],
            "late": int(sum(sum(r["late"]) for r in a)), "lo_add_max_ns": float(1e9 * max(abs(r["lo_add"] or 0.0) for r in recs)),
            "diverged": bool(recs[-1].get("diverged"))}


# ---- the trade-off (RL reward = -cost; the physics grid minimises the same sum) ----
I_TGT = -15.625


def cost(r, w_vo=1.0):
    """One period: hard turn-on (the largest V_DS above V_HARD, per 2 V), peak above 192 A (squared, per 4 A), Vo
    outside +-1 % (squared, per 0.5 %, weight w_vo; the frozen design's s_m62 already reaches 17 mV), circulating
    current (each valley more than 10 A below the target, per 20 A, weight 0.1)."""
    c_von = max(max(r["von"]) - V_HARD, 0.0) / 2.0
    c_pk = (max(max(r["peak"]) - 192.0, 0.0) / 4.0) ** 2
    c_vo = w_vo * (max(abs(r["vo"] - VO) - 0.01, 0.0) / 0.005) ** 2
    c_dep = 0.1 * sum(max(I_TGT - 10.0 - v, 0.0) for v in r["valley"]) / 20.0
    return c_von + c_pk + c_vo + c_dep


class VS:
    """The volt-second law with gain g and a slew limit on the offset (ns per period; None = none)."""

    def __init__(self, g=1.0, slew_ns=None, rail_only=False):
        self.g, self.slew, self.rail_only, self.prev = g, slew_ns, rail_only, 0.0

    def __call__(self, vff, prev=None):
        tref, re, rs = (vff.tlp >> 8) * LSB, vff.volts(vff.rail), vff.volts(vff.rss)

        def add(ton1):
            x = self.g * ((tref if self.rail_only else ton1) * re - tref * rs) / VO
            if self.slew is not None:
                x = min(max(x, self.prev - self.slew * 1e-9), self.prev + self.slew * 1e-9)
            self.prev = x
            return x
        return add


# ---- stimuli: A124 rows and the training distribution ----
def draw(rng):
    """Line steps |dv| 1..6.4 V over 1..10 us (log-uniform), 70 %; load steps 20..62.5 A either sign, 30 %."""
    if rng.random() < 0.7:
        dv = float(rng.uniform(1.0, 6.4)) * (1 if rng.random() < 0.5 else -1)
        return ("line", dv, float(np.exp(rng.uniform(0.0, np.log(10.0)))))
    return ("load", float(rng.uniform(20.0, 62.5)) * (1 if rng.random() < 0.5 else -1))


def stim_of(st, t, t_step):
    vin, i_step = 48.0, 0.0
    if st[0] == "line":
        vin += st[1] * min(max((t - t_step) / (st[2] * 1e-6), 0.0), 1.0)
    elif st[0] == "load" and t >= t_step:
        i_step = st[1]
    return vin, i_step


class Env:
    """D63 + V_DS + scb_vff with phase 1's edge offset as the action (lo_add = A_NS x a, a in [-2, 3]). The step comes
    at T_ENV; an episode is `horizon` periods. Actor observation (all from the controller's own signals, transient
    features first): 0 rail excess (scb_vff rail - rss, V / 4), 1 Vin slope (V per period / 2), 2 loop Ton vs its
    low-pass (x 10), 3 phase 1's last valley vs the target (A / 10, clipped +-2: the crossing report), 4 last phase-1
    turn-on hard (A132's V_DS comparator, V_DS > V_HARD), 5 context: rss - 11.3 V. The anchor zeroes 0-4."""
    A_NS = 100.0
    T_ENV = 10e-6
    N_OBS, N_TRANS, N_CRITIC = 6, 5, 18

    def __init__(self, horizon=200, d=None, w_vo=1.0):
        self.d = d or design(64)
        self.horizon, self.w_vo = horizon, w_vo
        self._warm = warm(self.d)

    @staticmethod
    def anchor(O):
        O = np.array(O, dtype=float, copy=True)
        O[:, :Env.N_TRANS] = 0.0
        return O

    def reset(self, rng=None, st=None):
        import copy
        self.vm, self.s, self.vff, self.ton = copy.deepcopy(self._warm)
        self.st = st if st is not None else draw(rng)
        self.n, self.prev, self.vin_prev, self.recs = 0, None, 48.0, []
        return self._pre()

    def _pre(self):
        self.vin, self.i_step = stim_of(self.st, self.s["t"], self.T_ENV)
        self.sc, self.cap = self.vff(self.vin, self.ton)
        return self.obs()

    def obs(self):
        v, p = self.vff, self.prev
        tref = (v.tlp >> 8) * LSB
        o = [(v.volts(v.rail) - v.volts(v.rss)) / 4.0, (self.vin - self.vin_prev) / 2.0,
             10.0 * (self.ton - tref) / tref,
             float(np.clip((p["valley"][0] - I_TGT) / 10.0, -2, 2)) if p else 0.0,
             float(p["von"][0] > V_HARD) if p else 0.0, v.volts(v.rss) - 11.3]
        return np.array(o)

    def critic_obs(self, o=None):
        p = self.prev
        o = self.obs() if o is None else o
        if p is None:
            return np.concatenate([o, np.zeros(self.N_CRITIC - self.N_OBS)])
        x = [r / 12.0 - 1 for r in p["rails"]] + [v / 20.0 for v in p["valley"]] + [(p["vo"] - VO) / 0.01,
             p["ton"] / 40e-9 - 1, max(p["peak"]) / 150.0 - 1, p["period"] / 500e-9 - 1]
        return np.concatenate([o, x])

    def step(self, a):
        return self.step_add(self.A_NS * float(np.clip(np.ravel(a)[0], -2.0, 3.0)) * 1e-9)

    def step_add(self, add):
        """One period with phase 1's offset add (s, or a function of Ton1 as from a law)."""
        r = self.vm.period(self.s, self.vin, self.i_step, ton_scale=self.sc, ton_cap=self.cap, lo_add=add)
        r["vin"], r["lo_add"] = self.vin, (add(r["tons"][0]) if callable(add) else add)
        self.recs.append(r)
        self.ton, self.prev, self.vin_prev = r["ton"], r, self.vin
        self.n += 1
        bad = not all(math.isfinite(x) and abs(x) < DIVERGED_A for x in r["valley"] + r["peak"])
        if bad:
            return self.obs(), -100.0, True, {"terminal": True}
        o = self._pre()
        return o, -cost(r, self.w_vo), self.n >= self.horizon, {}
