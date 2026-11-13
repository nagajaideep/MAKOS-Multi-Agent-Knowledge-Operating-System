"""Download the real data for the federal_contracts pack.

    python data/scripts/download_federal.py                  # FY2024, GSA awards
    python data/scripts/download_federal.py --agency "Department of the Interior"
    python data/scripts/download_federal.py --only far       # just one part

Saves into data/raw/federal_contracts/:
  usaspending/   contract transactions (zip of CSVs) from the USAspending bulk API
  sam/           SAM.gov exclusions public extract (source.zip from OpenSanctions)
  far/           FAR part 9 at two dates, from the eCFR point-in-time API
and writes SHA-256 checksums to data/raw/federal_contracts/CHECKSUMS.txt.

All sources are public; no API key needed. Large requests are retried.
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from makos.core.packs import load_pack  # noqa: E402

OUT = ROOT / "data" / "raw" / "federal_contracts"
UA = {"User-Agent": "MAKOS academic research project (non-commercial)"}

USASPENDING_BULK = "https://api.usaspending.gov/api/v2/bulk_download/awards/"
OPENSANCTIONS_INDEX = "https://data.opensanctions.org/datasets/latest/us_sam_exclusions/index.json"
OPENSANCTIONS_FALLBACK = ("https://data.opensanctions.org/artifacts/us_sam_exclusions/"
                          "20261112075506-blx/source.zip")


def _request(url: str, data: dict | None = None, timeout: int = 300, tries: int = 6) -> bytes:
    body = json.dumps(data).encode() if data is not None else None
    headers = dict(UA, **({"Content-Type": "application/json"} if body else {}))
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code != 429:
                detail = e.read()[:500].decode(errors="replace")
                raise SystemExit(f"HTTP {e.code} from {url}: {detail}")
            err = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            err = e
        wait = min(10 * 2 ** (attempt - 1), 120)
        print(f"  retry {attempt}/{tries - 1} in {wait}s ({err})")
        time.sleep(wait)
    raise SystemExit(f"failed after {tries} tries: {url}")


def _save(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    print(f"  saved {path.relative_to(ROOT)} ({len(content) / 1e6:.1f} MB)")


def download_usaspending(agency: str, start: str, end: str) -> None:
    print(f"USAspending: contract transactions awarded by {agency}, {start} to {end}")
    payload = {
        "filters": {
            "agencies": [{"type": "awarding", "tier": "toptier", "name": agency}],
            "prime_award_types": ["A", "B", "C", "D"],  # definitive contracts, purchase/delivery orders, BPA calls
            "date_type": "action_date",
            "date_range": {"start_date": start, "end_date": end},
        },
        "file_format": "csv",
    }
    job = json.loads(_request(USASPENDING_BULK, payload))
    print(f"  job {job['file_name']} queued; waiting for USAspending to build the file ...")
    status_url = job["status_url"]
    for _ in range(240):  # up to ~40 minutes
        st = json.loads(_request(status_url, timeout=60))
        state = st.get("status")
        if state == "finished":
            break
        if state == "failed":
            raise SystemExit(f"USAspending job failed: {st.get('message')}")
        print(f"  status: {state} ({st.get('total_rows') or '?'} rows so far)")
        time.sleep(10)
    else:
        raise SystemExit("USAspending job did not finish in 40 minutes; run again later")
    name = f"contracts_{agency.replace(' ', '_')}_{start}_{end}.zip"
    _save(OUT / "usaspending" / name, _request(job["file_url"], timeout=1800))


def download_sam() -> None:
    print("SAM.gov exclusions (public extract with UEI, via OpenSanctions source mirror)")
    url = OPENSANCTIONS_FALLBACK
    try:
        index = json.loads(_request(OPENSANCTIONS_INDEX, timeout=60, tries=2))
        for res in index.get("resources", []):
            if res.get("name") == "source.zip":
                url = res["url"]
                break
    except SystemExit:
        print("  index not available, using the pinned artifact URL")
    _save(OUT / "sam" / f"sam_exclusions_source_{date.today().isoformat()}.zip", _request(url))


def download_far() -> None:
    print("FAR part 9 (eCFR point-in-time versions)")
    pack = load_pack("federal_contracts")
    for ed in pack.editions:
        _save(pack.raw_dir / ed.filename, _request(ed.url, timeout=300))


def write_checksums() -> None:
    lines = []
    for f in sorted(p for p in OUT.rglob("*") if p.is_file() and p.name != "CHECKSUMS.txt"):
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        lines.append(f"{digest}  {f.relative_to(OUT).as_posix()}  downloaded {date.today().isoformat()}")
    (OUT / "CHECKSUMS.txt").write_text("\n".join(lines) + "\n")
    print(f"checksums written to {(OUT / 'CHECKSUMS.txt').relative_to(ROOT)}")


def main() -> None:
    pack = load_pack("federal_contracts")
    defaults = pack.extra["extra_sources"]["usaspending"]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agency", default=defaults["default_agency"])
    ap.add_argument("--start", default=defaults["default_period"][0])
    ap.add_argument("--end", default=defaults["default_period"][1])
    ap.add_argument("--only", choices=["usaspending", "sam", "far"])
    args = ap.parse_args()

    if args.only in (None, "far"):
        download_far()
    if args.only in (None, "sam"):
        download_sam()
    if args.only in (None, "usaspending"):
        download_usaspending(args.agency, args.start, args.end)
    write_checksums()


if __name__ == "__main__":
    main()
