"""A65 - digitize TI LMG1210 Figures 1 and 2 (peak source / sink current vs output voltage).

EXTERNAL_DEVICE_DATA. The datasheet (SNOSD12D, Nov 2018, rev. Jan 2019) is not
redistributed; pass its path. Both curves are vector paths on page 8; the axes
are fitted by least squares to the numeric tick labels (bottom row = x axis,
the rest = y axis), as for the EPC2067 figures in A57/A59/A60.

Output: lmg1210_output_iv.csv (v_out_v, i_source_a, i_sink_a on a 0.05 V grid)
and lmg1210_output_iv_digitization.json (hash, axis fits, residuals).

Usage: python3 digitize_lmg1210_output_iv.py <lmg1210.pdf>
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pymupdf

HERE = Path(__file__).resolve().parent
EXPECTED_SHA256 = "bf61f8480388e65d8bd8865db921f56bcdf2f00d869ad9881e3940848b7e352a"
SOURCE_URL = "https://www.ti.com/lit/ds/symlink/lmg1210.pdf"
PAGE = 7                      # 0-based: printed page 8, "6.7 Typical Characteristics"
FIGURES = {                   # path index on the page, label search box (x0, x1, y0, y1)
    "source": (165, (60, 300, 90, 255)),
    "sink": (184, (310, 545, 90, 255)),
}
GRID_V = np.round(np.arange(0.0, 5.0001, 0.05), 2)


def number(s):
    try:
        return float(s)
    except ValueError:
        return None


def axis_fit(words, box):
    x0, x1, y0, y1 = box
    ws = [w for w in words if x0 <= w[0] <= x1 and y0 <= w[1] <= y1 and number(w[4]) is not None]
    rows = {}
    for w in ws:
        rows.setdefault(round(w[1]), []).append(w)
    bottom = max(rows, key=lambda y: len(rows[y]))
    xl = rows[bottom]
    yl = [w for w in ws if round(w[1]) != bottom]
    xs, xv = [(w[0] + w[2]) / 2 for w in xl], [number(w[4]) for w in xl]
    ys, yv = [(w[1] + w[3]) / 2 for w in yl], [number(w[4]) for w in yl]
    ax, ay = np.polyfit(xs, xv, 1), np.polyfit(ys, yv, 1)
    return {"x_fit": ax.tolist(), "y_fit": ay.tolist(),
            "x_ticks": sorted(xv), "y_ticks": sorted(yv),
            "x_resid_max": float(np.max(np.abs(np.polyval(ax, xs) - xv))),
            "y_resid_max": float(np.max(np.abs(np.polyval(ay, ys) - yv)))}


def path_points(drawing):
    pts = []
    for item in drawing["items"]:
        if item[0] == "l":
            pts += [item[1], item[2]]
        elif item[0] == "c":
            pts += [item[1], item[4]]
    return np.array([(p.x, p.y) for p in pts])


def main(pdf):
    raw = Path(pdf).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"unexpected datasheet hash {digest}")
    page = pymupdf.open(pdf)[PAGE]
    text = page.get_text()
    for caption in ("Figure 1. Peak Source Current vs Output Voltage",
                    "Figure 2. Peak Sink Current vs Output Voltage"):
        if caption not in text:
            raise SystemExit(f"caption not found: {caption}")
    words, drawings = page.get_text("words"), page.get_drawings()
    meta = {"source_url": SOURCE_URL, "sha256": digest, "page_index": PAGE,
            "classification": "EXTERNAL_DEVICE_DATA", "conditions": "datasheet typical curves (VDD = 5 V)",
            "figures": {}}
    curves = {}
    for name, (index, box) in FIGURES.items():
        fit = axis_fit(words, box)
        xy = path_points(drawings[index])
        v = np.polyval(fit["x_fit"], xy[:, 0])
        i = np.polyval(fit["y_fit"], xy[:, 1])
        order = np.argsort(v)
        v, i = v[order], i[order]
        curves[name] = np.interp(GRID_V, v, i)
        meta["figures"][name] = {**fit, "path_index": index, "points": int(len(v)),
                                 "v_range": [float(v.min()), float(v.max())]}
    with open(HERE / "lmg1210_output_iv.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["v_out_v", "i_source_a", "i_sink_a"])
        for k, vv in enumerate(GRID_V):
            w.writerow([f"{vv:.2f}", f"{curves['source'][k]:.4f}", f"{curves['sink'][k]:.4f}"])
    (HERE / "lmg1210_output_iv_digitization.json").write_text(json.dumps(meta, indent=1))
    for name in FIGURES:
        f = meta["figures"][name]
        print(f"{name}: {f['points']} points, x resid {f['x_resid_max']:.2e} V, y resid {f['y_resid_max']:.2e} A")


if __name__ == "__main__":
    main(sys.argv[1])
