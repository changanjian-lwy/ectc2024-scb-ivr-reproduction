"""D74: steady three-dimensional heat conduction for the P24 module stack, with its analytic references.

Solver: cell-centred finite volumes on a rectilinear (non-uniform) grid, orthotropic conductivity per cell (kx, ky, kz),
heat per cell (W). Neighbour conductance A / (d_i / 2k_i + d_j / 2k_j) (harmonic, exact for a layered 1D path). Faces
are adiabatic unless given a convective condition -k dT/dn = h (T - T_f) (conductance A / (d / 2k + 1 / h)) or a fixed
temperature. Sparse direct solve (SuperLU); `Solver` keeps the factorisation so an electrothermal iteration that only
changes the heat reuses it.

Analytic references (used by tests/test_p24_thermal.py and diagnostics/D74_verification.json):
- slab with uniform generation, one face adiabatic, the other convective (quadratic profile);
- multilayer orthotropic rectangular flux channel with a rectangular isoflux source on the top face, adiabatic sides
  and a convective bottom: the Fourier-series solution of Muzychka, Culham and Yovanovich (J. Electron. Packag. 125,
  2003) for one layer, of Yovanovich, Muzychka and Culham (J. Thermophys. Heat Transf. 13, 1999) for two, written here
  as a layer-by-layer impedance recursion so any number of orthotropic layers is exact;
- effective conductivity of a square array of cylindrical copper vias in a matrix (parallel along the vias, Rayleigh
  / Maxwell-Garnett across them).
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

K_CU = 390.0          # W / (m K), plated copper
FACES = ("x0", "x1", "y0", "y1", "z0", "z1")


class Grid:
    """Rectilinear grid from cell-edge coordinates (m) in x, y, z."""

    def __init__(self, xe, ye, ze):
        self.xe, self.ye, self.ze = (np.asarray(e, float) for e in (xe, ye, ze))
        self.dx, self.dy, self.dz = np.diff(self.xe), np.diff(self.ye), np.diff(self.ze)
        if min(self.dx.min(), self.dy.min(), self.dz.min()) <= 0:
            raise ValueError("cell edges must increase")
        self.xc = 0.5 * (self.xe[1:] + self.xe[:-1])
        self.yc = 0.5 * (self.ye[1:] + self.ye[:-1])
        self.zc = 0.5 * (self.ze[1:] + self.ze[:-1])
        self.shape = (len(self.dx), len(self.dy), len(self.dz))
        self.n = int(np.prod(self.shape))

    def volume(self):
        return self.dx[:, None, None] * self.dy[None, :, None] * self.dz[None, None, :]

    def box(self, x=(-np.inf, np.inf), y=(-np.inf, np.inf), z=(-np.inf, np.inf)):
        """Boolean mask of cells whose centres lie in the half-open box [x0, x1) x [y0, y1) x [z0, z1)."""
        mx = (self.xc >= x[0]) & (self.xc < x[1])
        my = (self.yc >= y[0]) & (self.yc < y[1])
        mz = (self.zc >= z[0]) & (self.zc < z[1])
        return mx[:, None, None] & my[None, :, None] & mz[None, None, :]


def edges(breaks, max_step):
    """Cell edges through every break point, no cell wider than max_step (m)."""
    out = [breaks[0]]
    for a, b in zip(breaks[:-1], breaks[1:]):
        n = max(1, int(np.ceil((b - a) / max_step - 1e-9)))
        out.extend(a + (b - a) * np.arange(1, n + 1) / n)
    return np.array(out)


def _face_g(d1, k1, d2, k2, area):
    return area / (0.5 * d1 / k1 + 0.5 * d2 / k2)


class Solver:
    """Assembles the conduction matrix once; solve(q) for any heat map q (W per cell).

    bc: {face: ("h", h, t_f) | ("T", t) }; h may be a scalar or an array over the face's cells. Missing faces are
    adiabatic. method "direct": SuperLU with a symmetric minimum-degree ordering, factorised once; "cg": conjugate
    gradients preconditioned by the exact inverse of each z-column's tridiagonal part (thin layers couple strongly
    in z), relative residual rtol."""

    def __init__(self, grid, kx, ky, kz, bc, method="direct", rtol=1e-11):
        g = grid
        nx, ny, nz = g.shape
        kx, ky, kz = (np.broadcast_to(np.asarray(k, float), g.shape) for k in (kx, ky, kz))
        if min(kx.min(), ky.min(), kz.min()) <= 0:
            raise ValueError("conductivity must be positive")
        idx = np.arange(g.n).reshape(g.shape)
        rows, cols, vals = [], [], []
        diag = np.zeros(g.shape)
        ax = g.dy[None, :, None] * g.dz[None, None, :]
        ay = g.dx[:, None, None] * g.dz[None, None, :]
        az = g.dx[:, None, None] * g.dy[None, :, None]
        for axis, k, d, a in ((0, kx, g.dx, ax), (1, ky, g.dy, ay), (2, kz, g.dz, az)):
            sl0 = [slice(None)] * 3
            sl1 = [slice(None)] * 3
            sl0[axis], sl1[axis] = slice(None, -1), slice(1, None)
            sl0, sl1 = tuple(sl0), tuple(sl1)
            dsh = [1, 1, 1]
            dsh[axis] = -1
            dd = d.reshape(dsh)
            area = np.broadcast_to(a, g.shape)[sl0]
            gf = _face_g(np.broadcast_to(dd, g.shape)[sl0], k[sl0], np.broadcast_to(dd, g.shape)[sl1], k[sl1], area)
            i0, i1 = idx[sl0].ravel(), idx[sl1].ravel()
            rows += [i0, i1]
            cols += [i1, i0]
            vals += [-gf.ravel(), -gf.ravel()]
            diag[sl0] += gf
            diag[sl1] += gf
        self.rhs_bc = np.zeros(g.shape)
        self.face_g = {}
        for face, spec in (bc or {}).items():
            axis = "xyz".index(face[0])
            end = int(face[1])
            sl = [slice(None)] * 3
            sl[axis] = -1 if end else 0
            sl = tuple(sl)
            d = (g.dx, g.dy, g.dz)[axis][-1 if end else 0]
            k = (kx, ky, kz)[axis][sl]
            area = (ax, ay, az)[axis]
            area = np.broadcast_to(area, g.shape)[sl]
            if spec[0] == "h":
                h = np.broadcast_to(np.asarray(spec[1], float), k.shape)
                gb = area / (0.5 * d / k + 1.0 / h)
                t_ref = spec[2]
            elif spec[0] == "T":
                gb = area / (0.5 * d / k)
                t_ref = spec[1]
            else:
                raise ValueError(f"unknown boundary {spec[0]!r}")
            diag[sl] += gb
            self.rhs_bc[sl] += gb * t_ref
            self.face_g[face] = (sl, gb, t_ref)
        rows.append(idx.ravel())
        cols.append(idx.ravel())
        vals.append(diag.ravel())
        a = sp.csc_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(g.n, g.n))
        self.grid, self.matrix, self.method, self.rtol = g, a, method, rtol
        self.iterations = 0
        if method == "direct":
            self.lu = spla.splu(a, permc_spec="MMD_AT_PLUS_A", options={"SymmetricMode": True})
        elif method == "cg":
            zc = vals[4].size                     # z-direction couplings are the third axis pair (entries 4, 5)
            r = np.concatenate([rows[4], rows[5], idx.ravel()])
            c = np.concatenate([cols[4], cols[5], idx.ravel()])
            v = np.concatenate([vals[4], vals[5], diag.ravel()])
            assert vals[5].size == zc
            line = sp.csc_matrix((v, (r, c)), shape=(g.n, g.n))   # block tridiagonal in C order (z fastest)
            self.lu = spla.splu(line, permc_spec="NATURAL")
        else:
            raise ValueError(f"unknown method {method!r}")

    def solve(self, q, t0=None):
        q = np.broadcast_to(np.asarray(q, float), self.grid.shape)
        rhs = (q + self.rhs_bc).ravel()
        if self.method == "direct":
            t = self.lu.solve(rhs)
        else:
            m = spla.LinearOperator(self.matrix.shape, matvec=self.lu.solve)
            count = [0]

            def tick(_):
                count[0] += 1

            x0 = None if t0 is None else np.asarray(t0, float).ravel()
            t, info = spla.cg(self.matrix, rhs, x0=x0, rtol=self.rtol, maxiter=20000, M=m, callback=tick)
            self.iterations = count[0]
            if info != 0:
                raise RuntimeError(f"cg did not converge ({info})")
        return t.reshape(self.grid.shape)

    def set_face_ref(self, face, t_ref):
        """Change a convective or fixed face's reference temperature (scalar or per face cell); the matrix stays."""
        sl, gb, old = self.face_g[face]
        self.rhs_bc[sl] += gb * (np.asarray(t_ref, float) - np.asarray(old, float))
        self.face_g[face] = (sl, gb, t_ref)

    def face_heat(self, t):
        """Heat leaving through each non-adiabatic face (W)."""
        return {f: float(np.sum(gb * (t[sl] - tr))) for f, (sl, gb, tr) in self.face_g.items()}


def solve(grid, kx, ky, kz, q, bc, method="direct"):
    s = Solver(grid, kx, ky, kz, bc, method)
    t = s.solve(q)
    return t, s.face_heat(t)


# ---------------------------------------------------------------------------------------------------------------
# Analytic references


def slab_generation(x, length, k, qv, h, t_f):
    """1D slab 0 <= x <= length, uniform generation qv (W / m^3), adiabatic at 0, convective (h, t_f) at length."""
    return t_f + qv * length / h + qv * (length ** 2 - np.asarray(x, float) ** 2) / (2 * k)


def _top_impedance(beta, layers, h):
    """Flux / temperature-rise ratio at the top of a stack of orthotropic layers (top first: (t, kxy, kz)) over a
    convective base h, for in-plane wavenumber beta > 0."""
    hh = np.full_like(beta, float(h))
    for t, kxy, kz in reversed(layers):
        g = beta * np.sqrt(kxy / kz)          # decay rate in z
        kg = kz * g                           # = beta sqrt(kxy kz)
        th = np.tanh(g * t)
        hh = kg * (kg * th + hh) / (kg + hh * th)
    return hh


def flux_channel(a, b, layers, h, src, m_max=300, n_max=300):
    """Rectangular flux channel a x b (adiabatic sides), layers top first [(t, kxy, kz), ...], convective base h
    (sink at 0), isoflux source src = (xc, yc, c, d, q0) (centre, size along x / y, W / m^2) on the top face.

    Returns (mean temperature rise over the source, function (x, y) -> top-surface temperature rise)."""
    xc, yc, c, d, q0 = src
    m = np.arange(m_max + 1)
    n = np.arange(n_max + 1)
    lam = m * np.pi / a
    dlt = n * np.pi / b

    def cos_int(w, lo, hi, length):
        # (1 / length) integral of cos(w x) over [lo, hi], times 2 for w > 0 (cosine-series normalisation)
        out = np.where(w > 0, 2.0 * (np.sin(w * hi) - np.sin(w * lo)) / np.where(w > 0, w, 1.0), hi - lo)
        return out / length

    fx = cos_int(lam, xc - c / 2, xc + c / 2, a)        # source coefficient factors
    fy = cos_int(dlt, yc - d / 2, yc + d / 2, b)
    beta = np.sqrt(lam[:, None] ** 2 + dlt[None, :] ** 2)
    zero = beta == 0
    bsafe = np.where(zero, 1.0, beta)
    res = 1.0 / _top_impedance(bsafe, layers, h)       # temperature rise per unit flux of each mode
    res = np.where(zero, sum(t / kz for t, _, kz in layers) + 1.0 / h, res)
    coef = q0 * fx[:, None] * fy[None, :] * res
    # source mean of cos(lam x) cos(dlt y): (length / c) x the un-normalised integral
    gx = np.where(lam > 0, (np.sin(lam * (xc + c / 2)) - np.sin(lam * (xc - c / 2))) / np.where(lam > 0, lam, 1.0), c) / c
    gy = np.where(dlt > 0, (np.sin(dlt * (yc + d / 2)) - np.sin(dlt * (yc - d / 2))) / np.where(dlt > 0, dlt, 1.0), d) / d
    mean = float(np.sum(coef * gx[:, None] * gy[None, :]))

    def field(x, y):
        x = np.atleast_1d(np.asarray(x, float))
        y = np.atleast_1d(np.asarray(y, float))
        cx = np.cos(np.outer(x, lam))
        cy = np.cos(np.outer(y, dlt))
        return np.einsum("im,mn,in->i", cx, coef, cy)

    return mean, field


def via_k(f, k_via=K_CU, k_m=1.1):
    """Effective (k_inplane, k_z) of a matrix with a volume fraction f of parallel cylindrical vias along z."""
    kz = f * k_via + (1 - f) * k_m
    kxy = k_m * ((1 + f) * k_via + (1 - f) * k_m) / ((1 - f) * k_via + (1 + f) * k_m)
    return kxy, kz


def via_count(f, area_m2, d_m):
    """Number of vias of diameter d giving fill fraction f over area."""
    return f * area_m2 / (np.pi * d_m ** 2 / 4)


# ---------------------------------------------------------------------------------------------------------------
# The P24 module stack (Fig. 5c-d order, bottom to top). Every number P24 does not print is a scenario value here.

K_SOLDER = 58.0       # SAC solder
K_ABF = 0.4           # ABF build-up dielectric (assumed)

STACK = {
    "module_y": 20e-3,     # one 250 W module on two of P24's 10 x 10 mm sites (20 EPC2067 = 185 mm^2)
    "col_w": 2.5e-3,       # phase column width (Fig. 5b), L1 next to the strip
    "n_ph": 4,
    "strip_half": 2.5e-3,  # half of the central Vo / GND / Vin strip (the other half belongs to the mirror module)
    "t_spreader": 200e-6, "k_spreader": K_CU,
    "t_attach": 25e-6, "k_attach": 50.0,                  # die attach (sintered silver / solder)
    "t_die": 518e-6, "t_junction": 20e-6, "k_si": 120.0,   # EPC2067 die (datasheet 518 um), heat in its top 20 um
    "k_fill": 0.8,                                         # mould / underfill between dies and around bumps
    "t_bump": 140e-6, "bump_frac": 0.55,                   # EPC2067 solder bars (120 um) + solder resist
    "t_abf": 30e-6, "t_cu": 86e-6, "cu_cov": 0.7, "t_cu_sig": 25e-6,       # Vo / GND copper each (D65)
    "f_mv": 0.02,                                          # electrical microvias in each ABF dielectric
    "mv_follow": True,                                     # thermal vias are stacked columns: ABF fill >= glass fill
    "t_g1": 300e-6, "t_g2": 300e-6, "k_glass": 1.1,
    "f_g1": 0.0,                                           # copper fill of glass 1 under the phase columns
    "f_strip": 0.10,                                       # copper fill of the strip in both glasses (Vo / GND / Vin)
    "k_ind_xy": 20.0, "k_ind_z": 2.0,                      # MPC spiral inductor body (copper spiral in a paste core)
    "dx": 0.25e-3, "dy": 0.25e-3, "nz_scale": 1,
    "h_bot": 2e4, "t_cool": 25.0, "h_top": 0.0, "t_top": 25.0,
}
LAYER_NAMES = ("spreader", "attach", "die", "junction", "bump", "abf_l1", "cu_gnd", "abf_l2", "cu_g1b", "glass1",
               "cu_g1t", "abf_m1", "cu_vo", "abf_m2", "cu_g2b", "glass2", "cu_g2t", "abf_u1", "cu_u", "abf_u2")
CU_LAYERS = ("cu_gnd", "cu_g1b", "cu_g1t", "cu_vo", "cu_g2b", "cu_g2t", "cu_u")
ABF_LAYERS = ("abf_l1", "abf_l2", "abf_m1", "abf_m2", "abf_u1", "abf_u2")


def die_layout(p):
    """Five EPC2067-area blocks per phase column (LS HS LS HS LS along y), drawn to the column width with the die's
    area (9.26 mm^2); symmetric about y = module_y / 2, so the half module [0, module_y / 2] has a mirror plane there."""
    area = 2.85e-3 * 3.25e-3
    ly = area / p["col_w"]
    pitch = p["module_y"] / 5
    out = []
    for k in range(p["n_ph"]):
        x0 = k * p["col_w"]
        for j, kind in enumerate(("ls", "hs", "ls", "hs", "ls")):
            yc = (j + 0.5) * pitch
            out.append({"phase": k + 1, "kind": kind, "x": (x0, x0 + p["col_w"]), "y": (yc - ly / 2, yc + ly / 2)})
    return out


def build(p):
    """Grid, conductivities and region masks of one module plus half the strip: half the module in y with a mirror
    plane, or the full module length with p["y_full"] (needed when the coolant flows along y)."""
    p = dict(STACK, **p)
    thick = {"spreader": p["t_spreader"], "attach": p["t_attach"], "die": p["t_die"] - p["t_junction"],
             "junction": p["t_junction"], "bump": p["t_bump"], "cu_gnd": p["t_cu"], "cu_vo": p["t_cu"],
             "glass1": p["t_g1"], "glass2": p["t_g2"]}
    # glass-core convention: a metal layer on each glass face (the via landing / routing layer), ABF outside it
    layers = [(name, thick.get(name, p["t_abf"] if name.startswith("abf") else p["t_cu_sig"])) for name in LAYER_NAMES]
    zb = np.concatenate([[0.0], np.cumsum([t for _, t in layers])])
    zmax = {"spreader": 50e-6, "die": 130e-6, "glass1": 50e-6, "glass2": 50e-6, "cu_gnd": 50e-6, "cu_vo": 50e-6}
    ze = [0.0]
    for (name, t), z0 in zip(layers, zb[:-1]):
        n = max(1, int(np.ceil(t / zmax.get(name, t) - 1e-9))) * p.get("nz_scale", 1)
        ze.extend(z0 + t * np.arange(1, n + 1) / n)
    xw = p["n_ph"] * p["col_w"]
    xb = [-p["strip_half"]] + [k * p["col_w"] for k in range(p["n_ph"] + 1)]
    dies = die_layout(p)
    y_max = p["module_y"] if p.get("y_full") else p["module_y"] / 2
    yb = sorted({0.0, y_max} | {y for d in dies for y in d["y"] if 0 < y < y_max})
    g = Grid(edges(xb, p["dx"]), edges(yb, p["dy"]), np.array(ze))
    zr = {name: (z0, z1) for (name, _), z0, z1 in zip(layers, zb[:-1], zb[1:])}
    lay = {name: g.box(z=zr[name]) for name in zr}
    strip = g.box(x=(-np.inf, 0.0))
    cols = g.box(x=(0.0, xw))
    die_mask = np.zeros(g.shape, bool)
    die_regions = []
    for d in dies:
        m = g.box(x=d["x"], y=d["y"])
        if m.any():
            die_regions.append(dict(d, mask=m))
            die_mask |= m
    kx = np.full(g.shape, p["k_fill"])
    kz = kx.copy()

    def put(mask, kxy, kzz):
        kx[mask] = kxy
        kz[mask] = kzz

    put(lay["spreader"], p["k_spreader"], p["k_spreader"])
    put(lay["attach"] & die_mask, p["k_attach"], p["k_attach"])
    put((lay["die"] | lay["junction"]) & die_mask, p["k_si"], p["k_si"])
    fb = p["bump_frac"]
    put(lay["bump"] & die_mask, p["k_fill"] * (1 + fb) / (1 - fb), fb * K_SOLDER + (1 - fb) * p["k_fill"])
    kg1 = via_k(p["f_g1"], K_CU, p["k_glass"])
    kst = via_k(p["f_strip"], K_CU, p["k_glass"])
    put(lay["glass1"], *via_k(0.0, K_CU, p["k_glass"]))
    put(lay["glass1"] & cols, *kg1)
    put(lay["glass1"] & strip, *kst)
    put(lay["glass2"] & strip, *kst)
    put(lay["glass2"] & cols, p["k_ind_xy"], p["k_ind_z"])
    for name in CU_LAYERS:
        c = p["cu_cov"]
        put(lay[name], c * K_CU + (1 - c) * K_ABF, c * K_CU + (1 - c) * K_ABF)
    for name in ABF_LAYERS:
        base = p["f_mv"]
        put(lay[name], *via_k(base, K_CU, K_ABF))
        if p["mv_follow"]:
            put(lay[name] & cols, *via_k(max(base, p["f_g1"]), K_CU, K_ABF))
            put(lay[name] & strip, *via_k(max(base, p["f_strip"]), K_CU, K_ABF))
    bc = {"z0": ("h", p["h_bot"], p["t_cool"])}
    if p["h_top"] > 0:
        bc["z1"] = ("h", p["h_top"], p["t_top"])
    return {"p": p, "grid": g, "kx": kx, "kz": kz, "lay": lay, "strip": strip, "cols": cols, "dies": die_regions,
            "die_mask": die_mask, "bc": bc, "z_layers": zr, "y_max": y_max, "y_mult": p["module_y"] / y_max}


def z_flux(m, t, z):
    """Downward heat (W, modelled part of the module) across the cell face nearest to height z, split into the strip
    and the columns."""
    g = m["grid"]
    k = int(np.argmin(np.abs(g.ze[1:-1] - z)))           # face between cells k and k + 1
    dz, kz = g.dz, m["kz"]
    gf = (g.dx[:, None] * g.dy[None, :]) / (0.5 * dz[k] / kz[:, :, k] + 0.5 * dz[k + 1] / kz[:, :, k + 1])
    down = gf * (t[:, :, k + 1] - t[:, :, k])
    strip = m["strip"][:, :, k]
    return {"strip": float(down[strip].sum()), "columns": float(down[~strip].sum()), "z": float(g.ze[k + 1])}


def heat_sources(m, src):
    """Heat map (W per cell) of the modelled part (half or full module) from per-module losses src (W, whole module):
    die {phase: (hs W, ls W)} per die; inductor (in glass 2 over the columns, equal per phase); gate (die layer,
    with the dies); caps (glass 1, uniform over the columns); loop (lower ABF copper over the columns); lat_cu
    (half in the GND copper, half in the Vo copper, column k weighted by the square of the current it carries,
    16 : 9 : 4 : 1 from L1 to L4, D65)."""
    g, lay, p = m["grid"], m["lay"], m["p"]
    vol = g.volume()
    q = np.zeros(g.shape)
    half = 1.0 / m["y_mult"]                              # share of every module total in the modelled part

    def spread(mask, watts):
        v = vol[mask].sum()
        if v > 0 and watts:
            q[mask] += watts * vol[mask] / v

    jn = lay["junction"]
    for i, d in enumerate(m["dies"]):
        w = src["die_list"][i] if "die_list" in src else src["die"][d["phase"]][0 if d["kind"] == "hs" else 1]
        full = 2.85e-3 * 3.25e-3
        cut = (min(d["y"][1], m["y_max"]) - d["y"][0]) / (d["y"][1] - d["y"][0])
        mask = d["mask"] & jn
        spread(mask, w * cut)
        d["area_check"] = vol[mask].sum() / (p["t_junction"] * full * cut)
    spread(lay["junction"] & m["die_mask"], half * src.get("gate", 0.0))
    ind_cols = src.get("inductor_cols") or [src.get("inductor", 0.0) / p["n_ph"]] * p["n_ph"]
    for k, wk in enumerate(ind_cols):
        spread(lay["glass2"] & g.box(x=(k * p["col_w"], (k + 1) * p["col_w"])), half * wk)
    spread(lay["glass1"] & m["cols"], half * src.get("caps", 0.0))
    spread(lay["cu_gnd"] & m["cols"], half * src.get("loop", 0.0))
    lat = src.get("lat_cu_cols") or list(src.get("lat_cu", 0.0) * LAT_WEIGHTS[: p["n_ph"]] / LAT_WEIGHTS[: p["n_ph"]].sum())
    for k, wk in enumerate(lat):
        colk = g.box(x=(k * p["col_w"], (k + 1) * p["col_w"]))
        for name in ("cu_gnd", "cu_vo"):
            spread(lay[name] & colk, half * 0.5 * wk)
    return q


LAT_WEIGHTS = np.array([16.0, 9.0, 4.0, 1.0])


def coupled(m, src25, a_sw, a_cu, method="direct", tol=1e-3, max_iter=80, coolant=None):
    """Electrothermal fixed point (the DVPD framework's loop, spatially resolved): every die's conduction loss at its
    own mean junction temperature, each column's inductor copper at its body's mean temperature, the lateral copper
    at the mean temperature of its two copper layers in that column; switching, gate, capacitor and loop losses fixed.

    src25 (whole module, 25 C): die_cond / die_fixed {phase: (hs, ls)} per die, inductor (copper), core (the inductor
    array's core loss, held constant, in the inductor body), lat_cu, gate, caps, loop.
    coolant {m_dot (kg/s through the modelled width), t_in, cp}: the z0 face exchanges heat with a coolant flowing along
    +y, channel by channel (each x column of cells carries m_dot dx / width): the fluid temperatures join the linear
    system (first-order upwind per channel, m_i cp (T_f,j - T_f,j-1) = G_j (T_w,j - T_f,j), energy exact, stable at any
    NTU) and the augmented matrix is factorised once (needs the full module length, y_full).
    Returns (T, stats, src at the fixed point, iterations, face heat)."""
    g, lay, p = m["grid"], m["lay"], m["p"]
    vol = g.volume()
    solver = Solver(g, m["kx"], m["kx"], m["kz"], m["bc"], method)
    colmask = [g.box(x=(k * p["col_w"], (k + 1) * p["col_w"])) for k in range(p["n_ph"])]
    ind_m = [lay["glass2"] & c for c in colmask]
    cu_m = [(lay["cu_gnd"] | lay["cu_vo"]) & c for c in colmask]
    lat25 = src25.get("lat_cu", 0.0) * LAT_WEIGHTS[: p["n_ph"]] / LAT_WEIGHTS[: p["n_ph"]].sum()

    def vmean(t, mk):
        return float((t * vol)[mk].sum() / vol[mk].sum())

    if coolant:
        assert m["y_mult"] == 1.0, "the coolant needs the full module length (y_full)"
        sl0, gb0, tref0 = solver.face_g["z0"]
        nx, ny, _ = g.shape
        ns, nf = g.n, nx * ny
        mdot_i = coolant["m_dot"] * g.dx / (g.xe[-1] - g.xe[0])
        cap = np.repeat(mdot_i * coolant["cp"], ny)                 # W/K per fluid cell, C order (i, j)
        wall = np.arange(ns).reshape(g.shape)[:, :, 0].ravel()       # solid cells on the z0 face
        fl = ns + np.arange(nf)
        gbf = np.asarray(gb0, float).ravel()
        up = (np.arange(nf) % ny) > 0                                # cells with an upstream neighbour
        rows = np.concatenate([wall, fl, fl, fl[up]])
        cols = np.concatenate([fl, wall, fl, fl[up] - 1])
        vals = np.concatenate([-gbf, -gbf, cap + gbf, -cap[up]])
        aug = sp.bmat([[solver.matrix, None], [None, sp.csc_matrix((nf, nf))]], format="csc")
        aug = (aug + sp.csc_matrix((vals, (rows, cols)), shape=(ns + nf, ns + nf))).tocsc()
        lu_aug = spla.splu(aug, permc_spec="MMD_AT_PLUS_A")
        rhs_s = solver.rhs_bc.copy()
        rhs_s[sl0] -= gb0 * tref0                                    # the face now sees the fluid, not t_ref
        rhs_f = np.where(up, 0.0, cap * coolant["t_in"])
    t = None
    t_die = [25.0] * len(m["dies"])
    t_ind = [25.0] * p["n_ph"]
    t_cu = [25.0] * p["n_ph"]
    for it in range(1, max_iter + 1):
        src = dict(src25)
        src["die_list"] = []
        for d, td in zip(m["dies"], t_die):
            j = 0 if d["kind"] == "hs" else 1
            src["die_list"].append(src25["die_cond"][d["phase"]][j] * (1 + a_sw * (td - 25)) + src25["die_fixed"][d["phase"]][j])
        src["inductor_cols"] = [(src25.get("inductor", 0.0) * (1 + a_cu * (ti - 25)) + src25.get("core", 0.0)) / p["n_ph"]
                                for ti in t_ind]
        src["lat_cu_cols"] = [w * (1 + a_cu * (tc - 25)) for w, tc in zip(lat25, t_cu)]
        if coolant:
            x = lu_aug.solve(np.concatenate([(heat_sources(m, src) + rhs_s).ravel(), rhs_f]))
            t_new, t_f = x[:ns].reshape(g.shape), x[ns:].reshape(nx, ny)
        else:
            t_new = solver.solve(heat_sources(m, src), t0=t)
        change = np.inf if t is None else float(np.abs(t_new - t).max())
        t = t_new
        t_die = [vmean(t, d["mask"] & lay["junction"]) for d in m["dies"]]
        t_ind = [vmean(t, mk) for mk in ind_m]
        t_cu = [vmean(t, mk) for mk in cu_m]
        if change < tol:
            break
    stats = region_stats(m, t)
    if coolant:
        q = gb0 * (t[:, :, 0] - t_f)
        t_out = t_f[:, -1]
        stats.update({"coolant_t_out_mean": float(np.sum(mdot_i * t_out) / np.sum(mdot_i)),
                      "coolant_t_out_max": float(t_out.max()), "coolant_t_f_max": float(t_f.max()),
                      "coolant_heat_w": float(q.sum()), "coolant_t_f": t_f})
    total = m["y_mult"] * float(heat_sources(m, src).sum())          # whole module
    stats.update({"p_total_w": total, "t_die_mean": t_die, "t_ind_cols": t_ind, "t_latcu_cols": t_cu,
                  "p_inductor_w": float(sum(src["inductor_cols"])), "p_dies_w": m["y_mult"] * float(sum(
                      w * min(1.0, (min(d["y"][1], m["y_max"]) - d["y"][0]) / (d["y"][1] - d["y"][0]))
                      for w, d in zip(src["die_list"], m["dies"])))})
    face = solver.face_heat(t)
    if coolant:
        face["z0"] = stats["coolant_heat_w"]
    return t, stats, src, it, face


def region_stats(m, t):
    """Max / volume-mean temperature of the junctions (per die and overall), the inductor body, the strip, and the
    vertical temperature at the column centre."""
    g, lay = m["grid"], m["lay"]
    vol = g.volume()
    jn = lay["junction"] & m["die_mask"]
    ind = lay["glass2"] & m["cols"]
    out = {"t_max": float(t.max()), "junction_max": float(t[jn].max()), "inductor_max": float(t[ind].max()),
           "inductor_mean": float((t * vol)[ind].sum() / vol[ind].sum())}
    for d in m["dies"]:
        mk = d["mask"] & lay["junction"]
        d["t_mean"] = float((t * vol)[mk].sum() / vol[mk].sum())
        d["t_max"] = float(t[mk].max())
    out["layers_mean"] = {name: float((t * vol)[mk & m["cols"]].sum() / vol[mk & m["cols"]].sum())
                          for name, mk in lay.items() if (mk & m["cols"]).any()}
    return out
