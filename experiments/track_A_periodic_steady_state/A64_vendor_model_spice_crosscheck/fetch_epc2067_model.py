"""A64 - fetch EPC's EPC2067 vendor SPICE model and verify it (EXTERNAL_DEVICE_DATA).

EPC's own download page answers HTTP 403 to non-browser clients, so the
library `EPCGaNLibrary.lib` is taken from public GitHub mirrors (BOUNDARY
Section 1). The `.subckt EPC2067 ... .ends` block is extracted, CRLF is
normalized to LF, and the block's SHA-256 must start with
`b1d201cc7ab403f7` (2734 characters) -- the value the four independent
mirrors agree on.

The library is copyrighted by Efficient Power Conversion Corporation. It is
written only to `vendor/` (git-ignored, see `.gitignore`) and must never be
committed to this public repository.

Usage:
    python3 fetch_epc2067_model.py            # tries the mirrors in order
    python3 fetch_epc2067_model.py --all      # fetches all four, checks all agree
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENDOR = HERE / "vendor"
OUT = VENDOR / "EPC2067.lib"
OUT_X = VENDOR / "EPC2067X.lib"
EXPECTED_PREFIX = "b1d201cc7ab403f7"
EXPECTED_LENGTH = 2734
MIRRORS = [
    ("vgreff/LTSpiceLibraries", "LTSpice/vglib/sub/EPCGaNLibrary.lib"),
    ("hadibadri/GaN-Power-Converter", "src/models/EPCGaNLibrary.lib"),
    ("adml-upm/ESA_parallel_GaN", "02 Simulations/00 ComonLibs/EPCGaNLibrary.lib"),
    ("Blade87/LTspice", "25-gallium_nitride/EPCGaNLibrary.lib"),
]
BLOCK_RE = re.compile(r"(?ims)^\.subckt\s+EPC2067\s.*?^\.ends")


def fetch(repo: str, path: str) -> str:
    quoted = path.replace(" ", "%20")
    raw = subprocess.run(
        ["gh", "api", "-H", "Accept: application/vnd.github.raw",
         f"repos/{repo}/contents/{quoted}"],
        check=True, capture_output=True,
    ).stdout
    return raw.decode("latin-1").replace("\r\n", "\n")


def extract(text: str) -> tuple[str, str]:
    match = BLOCK_RE.search(text)
    if match is None:
        raise ValueError("no .subckt EPC2067 block found")
    block = match.group(0)
    return block, hashlib.sha256(block.encode("latin-1")).hexdigest()


def header_line(text: str) -> str:
    for line in text.splitlines():
        if "Copyright" in line and "Efficient Power Conversion" in line:
            return line.strip("* ").strip()
    return "(copyright header not found)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="fetch every mirror and require agreement")
    args = ap.parse_args()
    accepted = None
    for repo, path in MIRRORS:
        try:
            text = fetch(repo, path)
            block, digest = extract(text)
        except Exception as error:  # noqa: BLE001 - report and try the next mirror
            print(f"{repo}: FAILED ({error})")
            continue
        ok = digest.startswith(EXPECTED_PREFIX) and len(block) == EXPECTED_LENGTH
        print(f"{repo}: {len(block)} chars, sha256 {digest} -> {'OK' if ok else 'MISMATCH'}")
        if not ok:
            continue
        if accepted is None:
            accepted = (repo, block, digest, header_line(text))
        if not args.all:
            break
    if accepted is None:
        print("no mirror produced the expected EPC2067 block", file=sys.stderr)
        return 1
    repo, block, digest, header = accepted
    VENDOR.mkdir(exist_ok=True)
    OUT.write_text(
        f"* EPC2067 subcircuit extracted from EPCGaNLibrary.lib ({header})\n"
        f"* mirror: {repo}; block sha256 {digest}; NOT FOR REDISTRIBUTION\n"
        + block + "\n",
        encoding="latin-1",
    )
    print(f"wrote {OUT} (git-ignored)")
    xblock, changes = x_form(block)
    xdigest = hashlib.sha256(xblock.encode("latin-1")).hexdigest()
    OUT_X.write_text(
        f"* EPC2067X: EPC2067 from EPCGaNLibrary.lib ({header}) with the charge\n"
        "* expressions of C_CGS1/C_CGD1/C_CSD1 written in LTspice's own-voltage variable x\n"
        f"* (A64 x-form, see fetch_epc2067_model.py). Source block sha256 {digest};\n"
        f"* transformed block sha256 {xdigest}. NOT FOR REDISTRIBUTION\n" + xblock + "\n",
        encoding="latin-1",
    )
    for c in changes:
        print("  x-form:", c)
    print(f"wrote {OUT_X} (git-ignored), transformed block sha256 {xdigest}")
    return 0


def logical_lines(block: str) -> list[str]:
    """Join continuation lines ('+' at the start) of the three Q-capacitors only.

    Every other physical line is passed through unchanged.
    """
    out: list[str] = []
    joining = False
    for line in block.split("\n"):
        if line.startswith("+") and joining:
            out[-1] = out[-1].rstrip() + " " + line[1:].strip()
            continue
        joining = (line.split()[0] if line.strip() else "") in ("C_CGS1", "C_CGD1", "C_CSD1")
        out.append(line)
    return out


def x_form(block: str) -> tuple[str, list[str]]:
    """Rewrite the three charge-defined capacitors in terms of x (NUMERICAL, not physics).

    LTspice 26.0.2 integrates a `C ... Q=<expr>` capacitor correctly only when
    <expr> is written in x, the capacitor's own voltage; written with node
    voltages v(a,b) the element is not charge conserving (A64 RESULTS, model
    check: a 2 nF `Q=2n*v(d)` capacitor charged by 1 A absorbs 3.2 nC instead
    of 4 nC by 2 V at a 2 ps step, and diverges at 0.2 ps). The vendor model
    writes every nonlinear capacitance with v(...). For each capacitor whose
    charge depends only on its own terminal voltage the substitution
    v(n1,n2) -> x (n1, n2 = the element's own nodes, same order) is an
    identity. C_CGS1 also contains a 0.1 pF gate-source charge term driven by
    v(source,drain) (a trans-capacitance, not expressible in x); it is kept
    verbatim in a separate element C_CGS1B.
    """
    lines = logical_lines(block)
    out, changes = [], []
    own = {"C_CGS1": "v(gate,source)", "C_CGD1": "v(gate,drain)", "C_CSD1": "v(source,drain)"}
    for line in lines:
        name = line.split()[0] if line.strip() else ""
        if line.lower().startswith(".subckt epc2067 "):
            line = ".subckt EPC2067X" + line[len(".subckt EPC2067"):]
        if name in own:
            head, expr = line.split("Q=", 1)
            nodes = head.split()[1:3]
            if f"v({nodes[0]},{nodes[1]})" != own[name]:
                raise RuntimeError(f"unexpected node order in {name}")
            if name == "C_CGS1":
                inner = expr.strip()[1:-1]  # strip the outer parentheses
                terms = [t.strip() for t in inner.split(")+", 1)]
                first = terms[0] + ")"
                cross = terms[1]
                if "v(source,drain)" not in cross or "v(gate,source)" not in first:
                    raise RuntimeError("C_CGS1 terms not as expected")
                out.append(f"{head}Q=({first.replace(own[name], 'x')})")
                out.append(f"C_CGS1B gate source Q=({cross})")
                changes.append("C_CGS1: v(gate,source) -> x; v(source,drain) cross term moved verbatim to C_CGS1B")
            else:
                count = expr.count(own[name])
                others = [v for v in ("v(gate,source)", "v(gate,drain)", "v(source,drain)")
                          if v != own[name] and v in expr]
                if others:
                    raise RuntimeError(f"{name} depends on {others}")
                out.append(head + "Q=" + expr.replace(own[name], "x"))
                changes.append(f"{name}: {count} x {own[name]} -> x")
        else:
            out.append(line)
    if len(changes) != 3:
        raise RuntimeError(f"expected 3 capacitor rewrites, got {changes}")
    return "\n".join(out), changes


if __name__ == "__main__":
    raise SystemExit(main())
