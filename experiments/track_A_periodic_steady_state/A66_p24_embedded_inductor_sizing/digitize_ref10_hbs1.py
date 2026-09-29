"""A66 - digitize the HBS1 data of P24's inductor reference [10] (EXTERNAL_DEVICE_DATA).

C. Alvarez Barros et al., "Embedded Inductors Using Composite Magnetic
Materials for 12-1-V Integrated Voltage Regulators," IEEE TCPMT 11(12),
2183-2192, 2021, doi:10.1109/TCPMT.2021.3116946. The paper is not
redistributed; pass the path of the IEEE PDF. IEEE stamps every download
with the downloader and time, so the hash differs per copy: the script checks
the DOI and page count instead and records the hash of the copy used.

Page 5 (index 4) figures are vector paths. Axes are fitted to the grid lines
(the tick labels are outlined glyphs, not text):

- Fig. 8, "HBS1 Small Signal Racx": racx (mOhm/nH) vs duty cycle D, 6 inductor
  designs x {2, 5, 10} MHz, colours black / brown / light orange;
- Fig. 7, "Panasonic HBS1" inductance panel: measured L (nH) vs log f, 6
  designs (blue solid). Designs are assigned by descending L, in the
  figure's label order IND037, IND047, IND036, IND035, IND046, IND034.

Values typed from the paper's tables (page 4 and 7) are stored alongside.

Usage: python3 digitize_ref10_hbs1.py <ref10.pdf>
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pymupdf

HERE = Path(__file__).resolve().parent
DOI = "10.1109/TCPMT.2021.3116946"
PAGES = 10
PAGE = 4
RACX = {"x_grid": (2161, 2162, 2163, 2164, 2165, 2166), "x_values": (0, .2, .4, .6, .8, 1.0),
        "y_grid": (2167, 2174, 2181, 2188, 2195, 2202), "y_values": (0, 2, 4, 6, 8, 10),
        "curves": range(2223, 2241)}
RACX_COLOURS = {(0.0, 0.0, 0.0): "2MHz", (0.62, 0.39, 0.25): "5MHz", (1.0, 0.78, 0.5): "10MHz"}
IND = {"x_grid": (1386, 1387, 1388, 1389, 1390), "x_values": (-1, 0, 1, 2, 3),   # log10(f / MHz)
       "y_grid": (1391, 1397, 1403, 1409, 1415), "y_values": (0, 20, 40, 60, 80),
       "curves": (1519, 1521, 1523, 1525, 1527, 1529)}
IND_ORDER = ("IND037", "IND047", "IND036", "IND035", "IND046", "IND034")
D_GRID = [round(x, 4) for x in np.arange(0.05, 0.951, 0.01)] + [1 / 12]
# Typed from the paper (EXTERNAL_DEVICE_DATA)
TABLES = {
    "table_II_dcr_mohm": {"IND034": 14.3, "IND046": 13.6, "IND035": 21.3, "IND036": 24.9,
                          "IND047": 29.0, "IND048": 22.8, "IND037": 39.3},
    "table_IV_ind037_hbs1_5MHz": {
        "L_sm_nH": 69.8, "racx_mohm_per_nH": 0.753,
        "delta_i_mA": [77.24, 149.4, 227.6, 300.8, 373.9, 447.2, 513.2, 584.4],
        "L_nH": [77.06, 76.98, 75.62, 75.84, 75.65, 76.28, 76.48, 76.22],
        "P_ac_mW": [1.656, 6.609, 14.95, 26.55, 41.63, 59.87, 80.09, 105.2],
        "Racx_mohm_per_nH": [3.602, 3.847, 3.814, 3.869, 3.934, 3.925, 3.976, 4.043],
        "kappa": [4.786, 5.112, 5.068, 5.141, 5.227, 5.215, 5.283, 5.372]},
    "table_V_kappa_hbs1_D0p5": {"2MHz": 3.074, "3MHz": 4.134, "4MHz": 4.806, "5MHz": 5.069},
    "table_VI_ind048_hbs1": {"L_nH": 60.7, "R_dc_mohm": 22.8, "I_max_A": 5.0,
                             "racx_mohm_per_nH": 1.9, "racx_conditions": "10 MHz, D = 0.6",
                             "kappa": 5.1},
    "table_VII_target_12to1V_5MHz": {"racx_mohm_per_nH": 0.257, "kappa": 4.0, "mu_r": 65,
                                     "f_FMR_MHz": 25, "note": "a material that does not yet exist"},
    "eq_1_and_11": "P_L = I_dc^2 R_dc + (delta_i)^2 L kappa racx(D, f_s), delta_i = half peak-to-peak ripple",
}


def fit(drawings, grid, values):
    centre = lambda k, ax: ((drawings[k]["rect"].x0 + drawings[k]["rect"].x1) / 2 if ax == "x"  # noqa: E731
                            else (drawings[k]["rect"].y0 + drawings[k]["rect"].y1) / 2)
    pos = [centre(k, grid[0]) for k in grid[1]]
    coeff = np.polyfit(pos, values, 1)
    return coeff, float(np.max(np.abs(np.polyval(coeff, pos) - np.array(values))))


def curve(drawing, ax, ay):
    pts = []
    for item in drawing["items"]:
        if item[0] == "l":
            pts += [item[1], item[2]]
        elif item[0] == "c":
            pts += [item[1], item[4]]
    xy = np.array([(p.x, p.y) for p in pts])
    x, y = np.polyval(ax, xy[:, 0]), np.polyval(ay, xy[:, 1])
    order = np.argsort(x)
    return x[order], y[order]


def main(pdf):
    digest = hashlib.sha256(Path(pdf).read_bytes()).hexdigest()
    doc = pymupdf.open(pdf)
    if len(doc) != PAGES or DOI not in doc[0].get_text():
        raise SystemExit("not the expected paper (DOI / page count)")
    dr = doc[PAGE].get_drawings()
    out = {"source": "doi:10.1109/TCPMT.2021.3116946", "pdf_sha256": digest,
           "classification": "EXTERNAL_DEVICE_DATA", "tables": TABLES}
    ax, rx = fit(dr, ("x", RACX["x_grid"]), RACX["x_values"])
    ay, ry = fit(dr, ("y", RACX["y_grid"]), RACX["y_values"])
    racx = {}
    for k in RACX["curves"]:
        colour = tuple(round(c, 2) for c in dr[k]["color"])
        d, r = curve(dr[k], ax, ay)
        racx.setdefault(RACX_COLOURS[colour], []).append([float(np.interp(v, d, r)) for v in D_GRID])
    out["fig8_hbs1_racx"] = {"grid_residual": [rx, ry], "D": D_GRID,
                             "mohm_per_nH": racx}
    ax, rx = fit(dr, ("x", IND["x_grid"]), IND["x_values"])
    ay, ry = fit(dr, ("y", IND["y_grid"]), IND["y_values"])
    ls = []
    for k in IND["curves"]:
        lf, l = curve(dr[k], ax, ay)
        ls.append((float(np.interp(0.0, lf, l)), float(np.interp(np.log10(5.0), lf, l))))
    ls.sort(reverse=True)
    out["fig7_hbs1_inductance_nH"] = {"grid_residual": [rx, ry],
                                      "designs": {n: {"L_1MHz": a, "L_5MHz": b}
                                                  for n, (a, b) in zip(IND_ORDER, ls)}}
    (HERE / "ref10_hbs1_digitized.json").write_text(json.dumps(out, indent=1))
    k = D_GRID.index(1 / 12)
    for f, rows in racx.items():
        vals = [row[k] for row in rows]
        print(f"racx {f} at D = 1/12: {min(vals):.3f}-{max(vals):.3f} (mean {np.mean(vals):.3f}) mOhm/nH")
    for n, v in out["fig7_hbs1_inductance_nH"]["designs"].items():
        print(f"{n}: L {v['L_1MHz']:.1f} nH (1 MHz), {v['L_5MHz']:.1f} nH (5 MHz)")


if __name__ == "__main__":
    main(sys.argv[1])
