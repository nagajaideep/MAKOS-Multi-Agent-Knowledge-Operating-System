"""Download a domain pack's policy documents and verify their checksums.

    python data/scripts/download_policies.py bpi_p2p

Government sites are often slow or block scripts. If a download fails, open the
URL printed for it in your browser and save the file into data/raw/policy/
under the file name shown; then run this script again to verify it.
"""
from __future__ import annotations

import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from makos.core.packs import load_pack  # noqa: E402


def main() -> None:
    pack = load_pack(sys.argv[1] if len(sys.argv) > 1 else "bpi_p2p")
    raw = pack.raw_dir
    raw.mkdir(parents=True, exist_ok=True)
    problems = 0
    for ed in pack.editions:
        dest = raw / ed.filename
        if not dest.exists() and ed.url.lower().endswith(".pdf"):
            try:
                req = urllib.request.Request(ed.url, headers={"User-Agent": "Mozilla/5.0 makos-data-download"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    dest.write_bytes(r.read())
            except (urllib.error.URLError, TimeoutError) as err:
                print(f"FAILED  {ed.filename}: {err}\n        open in a browser: {ed.url}")
                problems += 1
                continue
        if not dest.exists():
            print(f"MANUAL  {ed.filename}: download from {ed.url} and save it under this name")
            problems += 1
            continue
        digest = hashlib.sha256(dest.read_bytes()).hexdigest()
        if ed.sha256 is None:
            print(f"NEW     {ed.filename}: sha256 {digest} (add to the pack's pack.yaml)")
        elif digest != ed.sha256:
            print(f"DIFFERS {ed.filename}: sha256 {digest} expected {ed.sha256}")
            problems += 1
        else:
            print(f"OK      {ed.filename}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
