"""Digitize EPC2067 Fig. 9 (typical normalized RDS(on) vs junction temperature).

Vector Bezier path of the curve, axes from a least-squares fit to the tick
labels. Writes the curve to CSV and provenance to JSON.

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
OUT_CSV = HERE / "epc2067_fig9_ron_vs_tj.csv"
OUT_META = HERE / "epc2067_fig9_digitization.json"
URL = "https://epc-co.com/epc/Portals/0/epc/documents/datasheets/epc2067_datasheet.pdf"
CLIP = pymupdf.Rect(330, 505, 592, 730)
COLOR = (0.0, 0.437, 0.729)


def main(pdf_path):
    for out in (OUT_CSV, OUT_META):
        if out.exists():
            raise SystemExit(f"refusing to overwrite {out.name}")
    raw = Path(pdf_path).read_bytes()
    doc = pymupdf.open(stream=raw, filetype="pdf")
    if "Revised October 21, 2021" not in doc[0].get_text():
        raise SystemExit("datasheet revision differs")
    page = doc[2]
    labels = []
    for w in page.get_text("words"):
        r = pymupdf.Rect(w[:4])
        if CLIP.contains(r):
            try:
                labels.append((float(w[4]), r))
            except ValueError:
                pass
    bottom = max(r.y0 for _, r in labels)
    xs = np.array(sorted((v, (r.x0 + r.x1) / 2) for v, r in labels if abs(r.y0 - bottom) < 1.0))
    ys = np.array(sorted((v, (r.y0 + r.y1) / 2) for v, r in labels if r.x1 < 350))
    fx, fy = np.polyfit(xs[:, 0], xs[:, 1], 1), np.polyfit(ys[:, 0], ys[:, 1], 1)
    res = dict(x_pt=float(np.max(np.abs(np.polyval(fx, xs[:, 0]) - xs[:, 1]))),
               y_pt=float(np.max(np.abs(np.polyval(fy, ys[:, 0]) - ys[:, 1]))))
    for drawing in page.get_drawings():
        if CLIP.intersects(drawing["rect"]) and (drawing.get("width") or 0) > 1.5 \
                and len(drawing["items"]) > 5 and np.allclose(tuple(drawing.get("color") or ()), COLOR, atol=0.01):
            pts = []
            for item in drawing["items"]:
                c = [np.array([q.x, q.y]) for q in item[1:]]
                if item[0] == "c":
                    t = np.linspace(0, 1, 100)[:, None]
                    pts.append((1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3])
                else:
                    pts.append(np.linspace(c[0], c[1], 30))
            pts = np.vstack(pts)
            break
    else:
        raise SystemExit("Fig. 9 curve not found")
    tj = (pts[:, 0] - fx[1]) / fx[0]
    k = (pts[:, 1] - fy[1]) / fy[0]
    order = np.argsort(tj)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["tj_c", "normalized_rds_on"])
        for a, b in zip(tj[order], k[order]):
            w.writerow([round(float(a), 4), round(float(b), 5)])
    k25 = float(np.interp(25.0, tj[order], k[order]))
    OUT_META.write_text(json.dumps(dict(
        source="EPC EPC2067 datasheet Fig. 9, typical normalized RDS(on) vs TJ, ID = 37 A, VGS = 5 V",
        category="EXTERNAL_DEVICE_DATA", url=URL, revision="Revised October 21, 2021",
        sha256=hashlib.sha256(raw).hexdigest(), tick_fit_max_residual=res,
        normalized_at_25c=k25,
        printed_rds_on_25c=dict(typ_mohm=1.3, max_mohm=1.55,
                                note="1.55 mOhm is the MAX column; typical is 1.3 mOhm")), indent=1) + "\n")
    print(f"wrote {OUT_CSV.name} ({len(tj)} points); k(25 C) = {k25:.4f}; residual {res}")


if __name__ == "__main__":
    main(sys.argv[1])
