"""Digitize EPC2067 Fig. 5a (Coss, linear scale) and Fig. 6 (Qoss, Eoss).

Curves come from the PDF vector paths (Bezier control points), axes from a
least-squares fit to tick-label positions (Fig. 6's right-axis label "0.34"
is a datasheet misprint on an evenly spaced 0.18 uJ axis and is excluded).
Writes per-device points to CSV and a provenance/cross-check JSON.

Usage: python3 digitize_epc2067_coss.py <path/to/epc2067_datasheet.pdf>
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pymupdf

HERE = Path(__file__).resolve().parent
OUT_CSV = HERE / "epc2067_coss_qoss_eoss_digitized.csv"
OUT_META = HERE / "epc2067_coss_digitization.json"
URL = "https://epc-co.com/epc/Portals/0/epc/documents/datasheets/epc2067_datasheet.pdf"
PAGE = 2
FIG5A = pymupdf.Rect(30, 50, 300, 262)
FIG6 = pymupdf.Rect(30, 280, 330, 500)
COSS_COLOR = (0.598, 0.12, 0.166)
QOSS_COLOR = (0.0, 0.437, 0.729)
EOSS_COLOR = (0.93, 0.112, 0.142)


def bezier(p0, p1, p2, p3, n=200):
    t = np.linspace(0.0, 1.0, n)[:, None]
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


def curve(page, clip, color, min_items=5):
    for drawing in page.get_drawings():
        if not clip.intersects(drawing["rect"]) or (drawing.get("width") or 0) < 1.5:
            continue
        if len(drawing["items"]) < min_items:
            continue  # legend swatches
        if np.allclose(tuple(drawing.get("color") or ()), color, atol=0.01):
            pts = []
            for item in drawing["items"]:
                ctrl = [np.array([q.x, q.y]) for q in item[1:]]
                pts.append(bezier(*ctrl) if item[0] == "c" else np.linspace(ctrl[0], ctrl[1], 40))
            return np.vstack(pts)
    raise SystemExit(f"curve {color} not found")


def ticks(page, clip):
    """x-axis labels are the bottom row (common, largest y0); the rest are
    left-axis (right edge left of the plot) or right-axis labels."""
    labels = []
    for w in page.get_text("words"):
        r = pymupdf.Rect(w[:4])
        if not clip.contains(r):
            continue
        try:
            labels.append((float(w[4]), r))
        except ValueError:
            continue
    bottom = max(r.y0 for _, r in labels)
    xs, left, right = [], [], []
    for value, r in labels:
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        if abs(r.y0 - bottom) < 1.0:
            xs.append((value, cx))
        elif r.x1 < clip.x0 + 36:
            left.append((value, cy))
        else:
            right.append((value, cy))
    return [np.array(sorted(v)) for v in (xs, left, right)]


def fit(pairs, exclude=()):
    keep = np.array([v not in exclude for v in pairs[:, 0]])
    coef = np.polyfit(pairs[keep, 0], pairs[keep, 1], 1)
    resid = float(np.max(np.abs(np.polyval(coef, pairs[keep, 0]) - pairs[keep, 1])))
    return coef, resid, sorted(set(pairs[~keep, 0].tolist()))


def to_data(pts, xfit, yfit, y_zero_pt=None):
    x = (pts[:, 0] - xfit[1]) / xfit[0]
    y0 = yfit[1] if y_zero_pt is None else y_zero_pt
    y = (pts[:, 1] - y0) / yfit[0]
    order = np.argsort(x)
    return x[order], y[order]


def main(pdf_path):
    for out in (OUT_CSV, OUT_META):
        if out.exists():
            raise SystemExit(f"refusing to overwrite {out.name}")
    raw = Path(pdf_path).read_bytes()
    doc = pymupdf.open(stream=raw, filetype="pdf")
    if "Revised October 21, 2021" not in doc[0].get_text():
        raise SystemExit("datasheet revision differs from device_library.py source_revision")
    page = doc[PAGE]

    x5, y5, _ = ticks(page, FIG5A)
    x5fit, x5res, _ = fit(x5)
    y5fit, y5res, _ = fit(y5)
    coss_v, coss_pf = to_data(curve(page, FIG5A, COSS_COLOR), x5fit, y5fit)

    x6, y6l, y6r = ticks(page, FIG6)
    x6fit, x6res, _ = fit(x6)
    y6lfit, y6lres, _ = fit(y6l)
    y6rfit, y6rres, excluded = fit(y6r, exclude=(0.34,))
    q_pts = curve(page, FIG6, QOSS_COLOR)
    e_pts = curve(page, FIG6, EOSS_COLOR)
    # both Fig. 6 curves start at the origin; anchor zero there (label-centre offset)
    q_v, q_nc = to_data(q_pts, x6fit, y6lfit, y_zero_pt=q_pts[np.argmin(q_pts[:, 0]), 1])
    e_v, e_uj = to_data(e_pts, x6fit, y6rfit, y_zero_pt=e_pts[np.argmin(e_pts[:, 0]), 1])

    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["curve", "vds_v", "value", "unit"])
        for v, c in zip(coss_v, coss_pf):
            w.writerow(["coss", round(float(v), 5), round(float(c), 3), "pF"])
        for v, q in zip(q_v, q_nc):
            w.writerow(["qoss", round(float(v), 5), round(float(q), 5), "nC"])
        for v, e in zip(e_v, e_uj):
            w.writerow(["eoss", round(float(v), 5), round(float(e), 6), "uJ"])
    OUT_META.write_text(json.dumps(dict(
        source="EPC EPC2067 datasheet, Fig. 5a (Coss, linear) and Fig. 6 (Qoss, Eoss), VGS = 0 V, typical, per device",
        category="EXTERNAL_DEVICE_DATA", url=URL, revision="Revised October 21, 2021",
        sha256=hashlib.sha256(raw).hexdigest(),
        method="PDF vector Bezier paths; axis maps least-squares on tick labels",
        tick_fit_max_residual_pt=dict(fig5a_x=x5res, fig5a_y=y5res, fig6_x=x6res, fig6_left=y6lres,
                                      fig6_right=y6rres),
        fig6_right_axis_labels_excluded=excluded,
        fig6_right_axis_note="label printed '0.34' on an evenly spaced 0.18 uJ axis (0.36 intended); excluded from the fit",
        printed_typical_values=dict(coss_20v_pf=1071, co_tr_0_20v_pf=1860, co_er_0_20v_pf=1597, qoss_20v_nc=37),
        printed_note="Coss 1607 pF and Qoss 56 nC are the MAX column, not typical"), indent=1) + "\n")
    print(f"wrote {OUT_CSV.name}: coss {len(coss_v)}, qoss {len(q_v)}, eoss {len(e_v)} points")


if __name__ == "__main__":
    main(sys.argv[1])
