"""Digitize EPC2067 datasheet Figure 8 (reverse drain-source characteristics).

Reads the curve Bezier control points straight from the PDF vector paths and
maps them to (VSD, ISD) with a least-squares fit to the tick-label positions.
Zero current is anchored to the curves' own flat ISD=0 segment (tick-label
text boxes are not glyph-centered). Writes the per-device curves to CSV and
the provenance (file hash, mapping, residuals) to JSON.

Usage: python3 digitize_epc2067_fig8.py <path/to/epc2067_datasheet.pdf>
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pymupdf

HERE = Path(__file__).resolve().parent
OUT_CSV = HERE / "epc2067_fig8_reverse_characteristics.csv"
OUT_META = HERE / "epc2067_fig8_digitization.json"
URL = "https://epc-co.com/epc/Portals/0/epc/documents/datasheets/epc2067_datasheet.pdf"
PAGE = 2  # zero-based; the page carrying Figure 8
CLIP = pymupdf.Rect(30, 505, 310, 730)  # Figure 8 region, PDF points
CURVES = {25: (0.0, 0.437, 0.729), 125: (0.93, 0.112, 0.142)}  # legend colors


def bezier(p0, p1, p2, p3, n=400):
    t = np.linspace(0.0, 1.0, n)[:, None]
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1
            + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


def main(pdf_path):
    for out in (OUT_CSV, OUT_META):
        if out.exists():
            raise SystemExit(f"refusing to overwrite {out.name}")
    raw = Path(pdf_path).read_bytes()
    page = pymupdf.open(stream=raw, filetype="pdf")[PAGE]
    text = page.get_text()
    if "Figure 8: Typical Reverse Drain-Source Characteristics" not in text.replace("\n", " ") \
            and "Figure 8" not in text:
        raise SystemExit("Figure 8 not found on the expected page")
    revision = "Revised October 21, 2021"
    if revision not in pymupdf.open(stream=raw, filetype="pdf")[0].get_text():
        raise SystemExit("datasheet revision differs from device_library.py source_revision")

    ticks_v, ticks_a = [], []
    for w in page.get_text("words"):
        r = pymupdf.Rect(w[:4])
        if not CLIP.contains(r):
            continue
        try:
            value = float(w[4])
        except ValueError:
            continue
        if r.y0 > 690:
            ticks_v.append((value, (r.x0 + r.x1) / 2))
        elif r.x1 < 63:
            ticks_a.append((value, (r.y0 + r.y1) / 2))
    ticks_v, ticks_a = np.array(sorted(ticks_v)), np.array(sorted(ticks_a))
    fit_v = np.polyfit(ticks_v[:, 0], ticks_v[:, 1], 1)  # x_pt = a*V + b
    fit_a = np.polyfit(ticks_a[:, 0], ticks_a[:, 1], 1)  # y_pt = c*A + d
    resid_v = float(np.max(np.abs(np.polyval(fit_v, ticks_v[:, 0]) - ticks_v[:, 1])))
    resid_a = float(np.max(np.abs(np.polyval(fit_a, ticks_a[:, 0]) - ticks_a[:, 1])))

    paths = {}
    for drawing in page.get_drawings():
        if not CLIP.intersects(drawing["rect"]) or (drawing.get("width") or 0) < 1.5:
            continue
        color = tuple(drawing.get("color") or ())
        for temp, ref in CURVES.items():
            if np.allclose(color, ref, atol=0.01):
                pts = []
                for item in drawing["items"]:
                    ctrl = [np.array([q.x, q.y]) for q in item[1:]]
                    pts.append(bezier(*ctrl) if item[0] == "c" else np.linspace(ctrl[0], ctrl[1], 50))
                paths[temp] = np.vstack(pts)
    if set(paths) != set(CURVES):
        raise SystemExit(f"curves found: {sorted(paths)}")

    # ISD=0 anchor: the flat leading segment common to both curves.
    y_zero = float(np.median([p[0, 1] for p in paths.values()]))
    label_zero_offset_a = (np.polyval(fit_a, 0.0) - y_zero) / -fit_a[0]
    rows = []
    for temp, pts in paths.items():
        v = (pts[:, 0] - fit_v[1]) / fit_v[0]
        a = (pts[:, 1] - y_zero) / fit_a[0]
        order = np.argsort(v)
        v, a = v[order], np.maximum(a[order], 0.0)
        a = np.maximum.accumulate(a)  # the drawn curves are monotone; remove sampling jitter
        for vv, aa in zip(v, a):
            rows.append((temp, round(float(vv), 5), round(float(aa), 4)))

    with OUT_CSV.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["temperature_c", "vsd_v", "isd_a_per_device"])
        writer.writerows(rows)
    OUT_META.write_text(json.dumps(dict(
        source="EPC EPC2067 datasheet, Figure 8, VGS = 0 V, typical, per device",
        category="EXTERNAL_DEVICE_DATA",
        url=URL, revision=revision, sha256=hashlib.sha256(raw).hexdigest(),
        method="PDF vector Bezier paths; axis map least-squares on tick labels; "
               "ISD=0 anchored to the curves' flat segment",
        volts_per_point=1 / fit_v[0], amps_per_point=1 / -fit_a[0],
        tick_fit_max_residual_pt=dict(voltage_axis=resid_v, current_axis=resid_a),
        tick_fit_max_residual=dict(volts=resid_v / fit_v[0], amps=resid_a / -fit_a[0]),
        label_center_vs_curve_zero_offset_a=float(label_zero_offset_a),
        table_value_for_comparison=dict(vsd_v=1.2, is_a=0.5, note="typ, defined by design"),
        note="negative OFF gate bias raises VSD (datasheet note); 0 V OFF assumed"),
        indent=1) + "\n")
    print(f"wrote {OUT_CSV.name} ({len(rows)} points) and {OUT_META.name}")


if __name__ == "__main__":
    main(sys.argv[1])
