"""Download the BPI Challenge 2019 event log (real purchase-to-pay data).

Source : 4TU.ResearchData, mirrored on figshare (article 12715853)
DOI    : 10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1
Licence: CC BY 4.0 - cite: van Dongen, B.F. (2019). BPI Challenge 2019.

The file (~695 MB) is NOT committed to git. Run:

    python data/scripts/download_bpi2019.py

It resumes partial downloads and writes the SHA-256 checksum to
data/raw/CHECKSUMS.txt so every teammate can confirm they have the same file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ARTICLE_ID = 12715853
API_URL = f"https://api.figshare.com/v2/articles/{ARTICLE_ID}/files"
RAW_DIR = Path(__file__).resolve().parents[1] / "raw"
CHUNK = 1 << 20  # 1 MiB


def list_files() -> list[dict]:
    req = urllib.request.Request(API_URL, headers={"User-Agent": "makos-data-download/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def download(url: str, dest: Path, expected_size: int | None, attempts: int = 8) -> None:
    """Download with resume; retry on server errors (figshare often returns 504)."""
    for attempt in range(1, attempts + 1):
        try:
            _download_once(url, dest, expected_size)
            return
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ConnectionError) as err:
            code = getattr(err, "code", None)
            if code and code < 500 and code != 429:
                raise
            if attempt == attempts:
                sys.exit(f"download failed after {attempts} tries ({err}). Run the script again to resume, "
                         "or download the file in your browser into data/raw/ (see data/README.md).")
            wait = min(10 * 2 ** (attempt - 1), 120)
            print(f"\nserver error ({err}); retry {attempt}/{attempts - 1} in {wait}s ...")
            time.sleep(wait)


def _download_once(url: str, dest: Path, expected_size: int | None) -> None:
    have = dest.stat().st_size if dest.exists() else 0
    if expected_size and have == expected_size:
        print(f"already downloaded: {dest.name}")
        return
    req = urllib.request.Request(url, headers={"User-Agent": "makos-data-download/1.0"})
    if have:
        req.add_header("Range", f"bytes={have}-")
        print(f"resuming {dest.name} at {have / 1e6:.1f} MB")
    with urllib.request.urlopen(req, timeout=120) as resp, dest.open("ab" if have else "wb") as out:
        done = have
        while True:
            block = resp.read(CHUNK)
            if not block:
                break
            out.write(block)
            done += len(block)
            if expected_size:
                print(f"\r{dest.name}: {done / 1e6:7.1f} / {expected_size / 1e6:.1f} MB", end="")
    print()
    if expected_size and dest.stat().st_size != expected_size:
        sys.exit(f"size mismatch for {dest.name}: got {dest.stat().st_size}, expected {expected_size}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="only list the files in the figshare article")
    args = ap.parse_args()

    files = list_files()
    for f in files:
        print(f"- {f['name']}  {f['size'] / 1e6:.1f} MB")
    if args.list:
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    for f in files:
        dest = RAW_DIR / f["name"]
        download(f["download_url"], dest, f.get("size"))
        digest = sha256_of(dest)
        lines.append(f"{digest}  {f['name']}  downloaded {date.today().isoformat()}")
        print(f"sha256 {digest}")
    (RAW_DIR / "CHECKSUMS.txt").write_text("\n".join(lines) + "\n")
    print(f"checksums written to {RAW_DIR / 'CHECKSUMS.txt'}")


if __name__ == "__main__":
    main()
