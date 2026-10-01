"""A90: digitise EPC2067 datasheet Fig. 9 (typical normalised RDS(on) vs junction temperature, ID = 37 A, VGS = 5 V).

As A57/A59: the curve from the PDF's vector Bezier paths, the axes from a least-squares fit to the tick-label centres.
Writes epc2067_fig9_rdson_vs_tj.csv and epc2067_fig9_digitization.json (provenance, tick residuals).
The PDF is not in this repository.

Usage: python3 digitize_epc2067_fig9.py <path/to/epc2067_datasheet.pdf>
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pymupdf

HERE = Path(__file__).resolve().parent
OUT_CSV = HERE / "epc2067_fig9_rdson_vs_tj.csv"
OUT_META = HERE / "epc2067_fig9_digitization.json"
URL = "https://epc-co.com/epc/Portals/0/epc/documents/datasheets/epc2067_datasheet.pdf"
PAGE = 2
FIG9 = pymupdf.Rect(318, 505, 600, 725)
COLOR = (0.0, 0.437, 0.729)


def bezier(p0, p1, p2, p3, n=200):
    t = np.linspace(0.0, 1.0, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def main(pdf_path):
    raw = Path(pdf_path).read_bytes()
    doc = pymupdf.open(stream=raw, filetype="pdf")
    if "Revised October 21, 2021" not in doc[0].get_text():
        raise SystemExit("datasheet revision differs from the one used in A57/A59/A86-A89")
    page = doc[PAGE]
    xs, ys = [], []
    for w in page.get_text("words"):
        r = pymupdf.Rect(w[:4])
        if not FIG9.contains(r):
            continue
        try:
            v = float(w[4])
        except ValueError:
            continue
        if abs(r.y0 - 695.6) < 1.0:                 # x-axis labels (TJ, deg C)
            xs.append((v, (r.x0 + r.x1) / 2))
        elif r.x1 < 350:                            # y-axis labels (normalised RDS(on))
            ys.append((v, (r.y0 + r.y1) / 2))
    xs, ys = np.array(sorted(xs)), np.array(sorted(ys))
    fx, fy = np.polyfit(xs[:, 0], xs[:, 1], 1), np.polyfit(ys[:, 0], ys[:, 1], 1)
    res_x = float(np.max(np.abs(np.polyval(fx, xs[:, 0]) - xs[:, 1])))
    res_y = float(np.max(np.abs(np.polyval(fy, ys[:, 0]) - ys[:, 1])))
    pts = []
    for d in page.get_drawings():
        if FIG9.intersects(d["rect"]) and (d.get("width") or 0) > 1.2 and np.allclose(d["color"], COLOR, atol=0.01):
            for it in d["items"]:
                c = [np.array([q.x, q.y]) for q in it[1:]]
                pts.append(bezier(*c) if it[0] == "c" else np.linspace(c[0], c[1], 40))
    p = np.vstack(pts)
    tj = (p[:, 0] - fx[1]) / fx[0]
    k = (p[:, 1] - fy[1]) / fy[0]
    o = np.argsort(tj)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["tj_c", "rds_on_normalized"])
        for a, b in zip(tj[o], k[o]):
            w.writerow([round(float(a), 4), round(float(b), 5)])
    OUT_META.write_text(json.dumps(dict(
        source="EPC EPC2067 datasheet, Fig. 9, typical normalised on-state resistance vs junction temperature, "
               "ID = 37 A, VGS = 5 V", category="EXTERNAL_DEVICE_DATA", url=URL, revision="Revised October 21, 2021",
        sha256=hashlib.sha256(raw).hexdigest(), method="PDF vector Bezier paths; axis maps least-squares on tick labels",
        tick_fit_max_residual_pt=dict(tj_axis=res_x, rds_axis=res_y),
        tick_fit_max_residual=dict(tj_c=res_x / fx[0], normalized=res_y / abs(fy[0])),
        values=dict((str(t), float(np.interp(t, tj[o], k[o]))) for t in (0, 25, 50, 75, 100, 125, 150))), indent=1) + "\n")
    print(f"wrote {OUT_CSV.name}: {len(tj)} points; 25 C {np.interp(25, tj[o], k[o]):.4f}, 125 C {np.interp(125, tj[o], k[o]):.4f}")


if __name__ == "__main__":
    main(sys.argv[1])
