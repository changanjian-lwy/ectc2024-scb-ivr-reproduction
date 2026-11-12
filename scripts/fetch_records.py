"""Fetch cosim records back from the GitHub release assets (records-*) into their places in the project.

Local records that a release holds are not kept in the working copy; experiments/RECORDS_MANIFEST.tsv lists each one
(path relative to the project, release tag). For each named experiment this downloads its releases, and writes every
archive member whose basename matches one of the manifest's paths to that path. Release copies have the home path
replaced by ~ (provenance only). Needs the gh CLI.
  python3 scripts/fetch_records.py A259 A258        # experiments by id
  python3 scripts/fetch_records.py --all
  python3 scripts/fetch_records.py A259 --root /some/dir   # write under another root (to check a copy)"""
from __future__ import annotations

import argparse
import re
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT / "experiments" / "RECORDS_MANIFEST.tsv"
REPO = "changanjian-lwy/ectc2024-scb-ivr-reproduction"


def members(asset):
    """(basename, bytes) of every run_*.json in a release asset, read in memory."""
    if asset.name.endswith((".tar.xz", ".tar.gz", ".tgz", ".tar")):
        with tarfile.open(asset, "r:*") as t:
            for m in t:
                if m.isfile() and re.search(r"run_[^/]*\.json$", m.name):
                    yield Path(m.name).name, t.extractfile(m).read()
    elif asset.name.endswith(".zip"):
        with zipfile.ZipFile(asset) as z:
            for n in z.namelist():
                if re.search(r"run_[^/]*\.json$", n):
                    yield Path(n).name, z.read(n)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ids", nargs="*", help="experiment ids, e.g. A259 C13")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--root", type=Path, default=PROJECT)
    a = ap.parse_args()
    rows = [line.split("\t") for line in MANIFEST.read_text().splitlines()[1:]]
    want = {i.upper() for i in a.ids}
    pick = [(p, tag) for p, tag in rows
            if a.all or any(re.match(rf"^{i}_", part) for part in Path(p).parts for i in want)]
    by_tag = {}
    for p, tag in pick:
        by_tag.setdefault(tag, {}).setdefault(Path(p).name, []).append(p)
    done = 0
    for tag, names in sorted(by_tag.items()):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["gh", "release", "download", tag, "-R", REPO, "-D", d], check=True)
            for asset in sorted(Path(d).iterdir()):
                for base, data in members(asset):
                    for p in names.get(base, []):
                        out = a.root / p
                        out.parent.mkdir(parents=True, exist_ok=True)
                        out.write_bytes(data)
                        done += 1
        print(tag, "done")
    print(f"{done} of {len(pick)} records written under {a.root}")


if __name__ == "__main__":
    main()
