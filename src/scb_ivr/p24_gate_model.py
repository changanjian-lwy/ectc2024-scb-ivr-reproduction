"""D79 / A163: a gate-level model of one EPC eGaN FET in the form of EPC's own SPICE model, for the package drive spec.

The vendor library is NOT in this repository (the repo is public). It is read at run time from the file named by the
environment variable SCB_EPC_LIB, else from <workspace>/vendor_models/EPCGaNLibrary.lib (three levels above the project
root); load_device() raises FileNotFoundError when neither exists, and the tests that need it skip.

Model (EPC's published model structure, evaluated per device at temperature temp, deg C):
- channel, drain -> source:  A1' ln(1 + exp((v_gs - k2') / k3)) v_ds / (1 + (x0_0' + x0_1' v_gs) v_ds) for v_ds > 0,
  the mirror with v_gd and v_sd for v_ds < 0 (third quadrant); primes = the temperature factors of the model;
- gate-source charge  q_gs = ags1 v_gs + 0.5 ags2 ags4 sp((v_gs - ags3) / ags4) + ags5 ags7 sp((v_sd - ags6) / ags7),
  gate-drain charge   q_gd = agd1 v_gd + 0.5 ags2 ags4 sp(...v_gd...) + three softplus terms (agd2..agd10),
  source-drain charge q_sd = asd1 v_sd + three softplus terms (asd2..asd10), sp(x) = ln(1 + e^x);
- series rd / rs (rpara split by rpara_s_factor, with its temperature factor), gate resistance rg_value;
  the gate-protection diodes (micro-amperes) are left out.
Device.c_iss / c_rss / c_oss / q_oss / rds_on / vth give the datasheet quantities; gate_charge() runs the datasheet's
gate-charge test (constant gate current, clamped inductive drain current) on the model.
"""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parents[2]
DEFAULT_LIB = PROJECT.parents[2] / "vendor_models" / "EPCGaNLibrary.lib"


def lib_path():
    p = os.environ.get("SCB_EPC_LIB")
    return Path(p) if p else DEFAULT_LIB


def _subckt(text, name):
    m = re.search(rf"^\.subckt\s+{re.escape(name)}\s.*?^\.ends", text, re.S | re.I | re.M)
    if m is None:
        raise KeyError(f"{name} not in the library")
    return m.group(0)


def _params(block):
    """The .param assignments of a subcircuit (continuation lines joined), evaluated in order."""
    lines, cur = [], None
    for ln in block.splitlines():
        s = ln.strip()
        if s.lower().startswith(".param"):
            cur = s[6:]
            lines.append(cur)
        elif s.startswith("+") and lines and cur is not None:
            lines[-1] += " " + s[1:]
        else:
            cur = None
    raw = {}
    for ln in lines:
        for k, v in re.findall(r"(\w+)\s*=\s*(\{[^}]*\}|[^\s]+)", ln):
            raw[k] = v.strip("{}")
    vals, todo = {}, dict(raw)
    for _ in range(len(todo) + 1):                       # resolve forward references
        for k in list(todo):
            try:
                vals[k] = float(eval(todo[k].replace("E", "e"), {"__builtins__": {}}, dict(vals)))
                del todo[k]
            except NameError:
                pass
        if not todo:
            break
    if todo:
        raise ValueError(f"unresolved parameters {sorted(todo)}")
    return vals


def _sp(x):
    return np.logaddexp(0.0, x)


def _sig(x):
    return 0.5 * (1.0 + np.tanh(0.5 * x))


@dataclass
class Device:
    name: str
    p: dict
    sha1: str
    temp: float = 25.0
    dk2: float = 0.0          # threshold shift (V) added to k2: a spread case, not part of EPC's model
    cg_scale: float = 1.0     # gate capacitances (q_gs, q_gd) times this: a spread case (datasheet C_ISS max / typ)

    # ---- temperature-dependent constants ----
    def _k(self):
        p, dt = self.p, self.temp - 25.0
        return (p["A1"] * (1 - p["aITc"] * dt), (p["k2"] + self.dk2) * (1 - p["k2Tc"] * dt), p["k3"],
                p["x0_0"] * (1 - p["x0_0_TC"] * dt), p["x0_1"] * (1 - p["x0_1_TC"] * dt))

    @property
    def r_d(self):
        p = self.p
        return (1 - p["rpara_s_factor"]) * p["rpara"] * (1 - p["arTc"] * (self.temp - 25.0))

    @property
    def r_s(self):
        p = self.p
        return p["rpara_s_factor"] * p["rpara"] * (1 - p["arTc"] * (self.temp - 25.0))

    @property
    def r_g(self):
        return self.p["rg_value"]

    # ---- channel ----
    def i_ch(self, vgs, vds):
        """Channel current drain -> source (A), internal nodes, both quadrants."""
        a1, k2, k3, x0, x1 = self._k()
        vgs, vds = np.asarray(vgs, float), np.asarray(vds, float)
        vgd = vgs - vds
        fwd = a1 * _sp((vgs - k2) / k3) * vds / (1 + (x0 + x1 * vgs) * vds)
        rev = -a1 * _sp((vgd - k2) / k3) * (-vds) / (1 + (x0 + x1 * vgd) * (-vds))
        return np.where(vds > 0, fwd, rev)

    def di_ch(self, vgs, vds, eps=1e-6):
        """(d i / d v_gs, d i / d v_ds), central differences."""
        gm = (self.i_ch(vgs + eps, vds) - self.i_ch(vgs - eps, vds)) / (2 * eps)
        gd = (self.i_ch(vgs, vds + eps) - self.i_ch(vgs, vds - eps)) / (2 * eps)
        return gm, gd

    # ---- charges and capacitances ----
    def q_gs(self, vgs, vsd=0.0):
        p = self.p
        return self.cg_scale * (p["ags1"] * vgs + 0.5 * p["ags2"] * p["ags4"] * _sp((vgs - p["ags3"]) / p["ags4"])
                                + p["ags5"] * p["ags7"] * _sp((vsd - p["ags6"]) / p["ags7"]))

    def c_gs(self, vgs, vsd=0.0):
        p = self.p
        return self.cg_scale * (p["ags1"] + 0.5 * p["ags2"] * _sig((vgs - p["ags3"]) / p["ags4"]))

    def q_gd(self, vgd):
        p = self.p
        q = p["agd1"] * vgd + 0.5 * p["ags2"] * p["ags4"] * _sp((vgd - p["ags3"]) / p["ags4"])
        for a, b, c in (("agd2", "agd3", "agd4"), ("agd5", "agd6", "agd7"), ("agd8", "agd9", "agd10")):
            q = q + p[a] * p[c] * _sp((vgd - p[b]) / p[c])
        return self.cg_scale * q

    def c_gd(self, vgd):
        p = self.p
        c = p["agd1"] + 0.5 * p["ags2"] * _sig((vgd - p["ags3"]) / p["ags4"])
        for a, b, cc in (("agd2", "agd3", "agd4"), ("agd5", "agd6", "agd7"), ("agd8", "agd9", "agd10")):
            c = c + p[a] * _sig((vgd - p[b]) / p[cc])
        return self.cg_scale * c

    def q_sd(self, vsd):
        p = self.p
        q = p["asd1"] * vsd
        for a, b, c in (("asd2", "asd3", "asd4"), ("asd5", "asd6", "asd7"), ("asd8", "asd9", "asd10")):
            q = q + p[a] * p[c] * _sp((vsd - p[b]) / p[c])
        return q

    def c_sd(self, vsd):
        p = self.p
        c = p["asd1"]
        for a, b, cc in (("asd2", "asd3", "asd4"), ("asd5", "asd6", "asd7"), ("asd8", "asd9", "asd10")):
            c = c + p[a] * _sig((vsd - p[b]) / p[cc])
        return c

    def q_gate(self, vgs, vds):
        """Charge on the internal gate node (q_gs + q_gd) at (v_gs, v_ds)."""
        return self.q_gs(vgs, -vds) + self.q_gd(vgs - vds)

    # ---- datasheet quantities ----
    def c_iss(self, vds=20.0):
        return float(self.c_gs(0.0, -vds) + self.c_gd(-vds))

    def c_rss(self, vds=20.0):
        return float(self.c_gd(-vds))

    def c_oss(self, vds=20.0):
        return float(self.c_gd(-vds) + self.c_sd(-vds))

    def q_oss(self, vds=20.0):
        """Output charge 0 -> vds at v_gs = 0 (q_sd and q_gd move by -vds)."""
        return float((self.q_sd(0.0) - self.q_sd(-vds)) + (self.q_gd(0.0) - self.q_gd(-vds)))

    def rds_on(self, vgs=5.0, i=37.0):
        """Terminal resistance at (v_gs, I): internal V_DS by bisection, plus rd + rs (gate at the internal source)."""
        lo, hi = 0.0, 5.0
        for _ in range(80):
            m = 0.5 * (lo + hi)
            lo, hi = (m, hi) if self.i_ch(vgs, m) < i else (lo, m)
        return 0.5 * (lo + hi) / i + self.r_d + self.r_s

    def vth(self, i=18e-3):
        """V_GS = V_DS at which the channel carries i (the datasheet's threshold test)."""
        lo, hi = 0.0, 5.0
        for _ in range(80):
            m = 0.5 * (lo + hi)
            lo, hi = (m, hi) if self.i_ch(m, m) < i else (lo, m)
        return 0.5 * (lo + hi)

    def vgs_for(self, i, vds):
        """v_gs at which the channel carries i at v_ds (bisection; i > 0, v_ds > 0)."""
        lo, hi = -1.0, 8.0
        for _ in range(80):
            m = 0.5 * (lo + hi)
            lo, hi = (m, hi) if self.i_ch(m, vds) < i else (lo, m)
        return 0.5 * (lo + hi)

    def gate_charge(self, vds0=20.0, i_d=37.0, i_g=10e-3, v_end=5.0, h=1e-11):
        """Datasheet gate-charge test on the model (internal nodes, no series resistances): a constant gate current
        charges the gate; the drain is clamped at vds0 while the channel carries less than i_d, then i_d discharges the
        node. Implicit Euler in (v_gs, v_ds), Newton per step. Returns Q when the channel first carries 1 % of i_d
        (q_th), at the plateau start (V_DS leaves the clamp, q_gs), when V_DS falls below 10 % / 1 % of vds0 (q_v10,
        q_v1), at v_end (q_g), the plateau voltage, and q_gd = q_v10 - q_gs (the plateau's charge)."""
        vgs, vds, q, out = 0.0, vds0, 0.0, {}
        clamped = True
        while vgs < v_end:
            if clamped:                                  # dq = i_g h on the gate only (v_ds fixed)
                q1 = q + i_g * h
                v = vgs
                for _ in range(50):
                    f = self.q_gate(v, vds) - self.q_gate(vgs, vds) - i_g * h
                    v -= f / (self.c_gs(v, -vds) + self.c_gd(v - vds))
                    if abs(f) < 1e-18:
                        break
                vgs, q = v, q1
                if "q_th" not in out and self.i_ch(vgs, vds) >= 0.01 * i_d:
                    out["q_th"] = q
                if self.i_ch(vgs, vds) >= i_d:
                    clamped = False
                    out["q_gs"], out["v_plateau"] = q, vgs
                continue
            # unclamped: gate: q_gate(v1, d1) - q_gate(v0, d0) = i_g h; drain node: q_sd/q_gd balance with i_d - i_ch
            v1, d1 = vgs, vds
            qg0, qd0 = self.q_gate(vgs, vds), -self.q_gd(vgs - vds) - self.q_sd(-vds)
            for _ in range(60):
                f1 = self.q_gate(v1, d1) - qg0 - i_g * h
                f2 = (-self.q_gd(v1 - d1) - self.q_sd(-d1)) - qd0 - (i_d - self.i_ch(v1, d1)) * h
                cgs, cgd, csd = self.c_gs(v1, -d1), self.c_gd(v1 - d1), self.c_sd(-d1)
                gm, gd = self.di_ch(v1, d1)
                j = np.array([[cgs + cgd, -cgs * 0.0 - cgd], [-cgd + gm * h, cgd + csd + gd * h]])
                dx = np.linalg.solve(j, [f1, f2])
                v1, d1 = v1 - dx[0], d1 - dx[1]
                if abs(dx[0]) < 1e-9 and abs(dx[1]) < 1e-9:
                    break
            vgs, vds, q = v1, d1, q + i_g * h
            if "q_v10" not in out and vds < 0.1 * vds0:
                out["q_v10"] = q
            if "q_v1" not in out and vds < 0.01 * vds0:
                out["q_v1"] = q
        out["q_g"] = q
        out["q_gd"] = out.get("q_v10", q) - out.get("q_gs", 0.0)
        return out


def load_device(name="EPC2067", path=None, **kw):
    path = Path(path) if path else lib_path()
    text = path.read_text(errors="replace")
    block = _subckt(text, name)
    return Device(name, _params(block), hashlib.sha1(block.encode()).hexdigest()[:10], **kw)


def available(name="EPC2067"):
    try:
        load_device(name)
        return True
    except (FileNotFoundError, KeyError):
        return False
