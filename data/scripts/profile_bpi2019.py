"""Profile the BPI Challenge 2019 log and convert it to tables.

    python data/scripts/profile_bpi2019.py data/raw/<file>.xes

Outputs
  data/interim/bpi2019_cases.parquet   one row per PO line item (case)
  data/interim/bpi2019_events.parquet  one row per event
  data/profile/bpi2019_profile.json    numbers used by later stages
  data/profile/bpi2019_profile.md      readable summary (commit this)

The script also checks its counts against the figures published for the
dataset, so a broken download or parser shows up immediately.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from xes_reader import iter_traces  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1]

# Figures published by the dataset owner and in BPIC 2019 reports.
PUBLISHED = {
    "cases": 251_734,
    "purchase_documents": 76_349,
    "events": 1_595_923,
    "activities": 42,
}

# Attribute names used in the BPI 2019 XES file.
CASE_ID = "concept:name"
ACTIVITY = "concept:name"
TIMESTAMP = "time:timestamp"
PO_DOC = "Purchasing Document"
ITEM_CATEGORY = "Item Category"
VENDOR = "Vendor"
AMOUNT = "Cumulative net worth (EUR)"


def load(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    case_rows, event_rows = [], []
    for i, (case, events) in enumerate(iter_traces(path), 1):
        cid = case.get(CASE_ID)
        case_rows.append(case)
        for seq, ev in enumerate(events):
            ev = {f"event_{k}" if k == CASE_ID else k: v for k, v in ev.items()}
            ev["case_id"] = cid
            ev["seq"] = seq
            event_rows.append(ev)
        if i % 25_000 == 0:
            print(f"  read {i:,} cases")
    cases = pd.DataFrame(case_rows).rename(columns={CASE_ID: "case_id"})
    events = pd.DataFrame(event_rows).rename(columns={f"event_{ACTIVITY}": "activity"})
    if TIMESTAMP in events:
        events[TIMESTAMP] = pd.to_datetime(events[TIMESTAMP], utc=True, errors="coerce")
    return cases, events


def profile(cases: pd.DataFrame, events: pd.DataFrame) -> dict:
    p: dict = {
        "cases": int(len(cases)),
        "events": int(len(events)),
        "activities": int(events["activity"].nunique()),
        "case_attributes": sorted(cases.columns.tolist()),
        "event_attributes": sorted(events.columns.tolist()),
    }
    if PO_DOC in cases:
        p["purchase_documents"] = int(cases[PO_DOC].nunique())
    if VENDOR in cases:
        p["vendors"] = int(cases[VENDOR].nunique())
    if ITEM_CATEGORY in cases:
        p["item_category_counts"] = cases[ITEM_CATEGORY].value_counts().to_dict()
    if TIMESTAMP in events:
        ts = events[TIMESTAMP].dropna()
        p["first_event"] = ts.min().isoformat()
        p["last_event"] = ts.max().isoformat()
        p["events_per_year"] = ts.dt.year.value_counts().sort_index().astype(int).to_dict()
    p["activity_counts"] = events["activity"].value_counts().astype(int).to_dict()
    lengths = events.groupby("case_id").size()
    p["events_per_case"] = {k: float(v) for k, v in lengths.describe().items()}
    p["missing_case_values"] = {c: int(n) for c, n in cases.isna().sum().items() if n}
    p["checks"] = {
        k: {"expected": v, "found": p.get(k), "ok": p.get(k) == v} for k, v in PUBLISHED.items()
    }
    return p


def to_markdown(p: dict) -> str:
    lines = ["# BPI Challenge 2019: data profile", ""]
    lines += ["## Checks against published figures", "", "| Measure | Expected | Found | OK |", "| --- | --- | --- | --- |"]
    for k, c in p["checks"].items():
        lines.append(f"| {k} | {c['expected']:,} | {c['found'] if c['found'] is None else format(c['found'], ',')} | {'yes' if c['ok'] else 'NO'} |")
    lines += ["", "## Overview", "",
              f"- Cases (PO line items): {p['cases']:,}",
              f"- Events: {p['events']:,}",
              f"- Distinct activities: {p['activities']}",
              f"- Purchase documents: {p.get('purchase_documents', 'n/a'):,}" if "purchase_documents" in p else "- Purchase documents: attribute not found",
              f"- Vendors: {p.get('vendors', 'n/a')}",
              f"- Event time range: {p.get('first_event')} to {p.get('last_event')}", ""]
    if "item_category_counts" in p:
        lines += ["## Item categories", "", "| Category | Cases |", "| --- | --- |"]
        lines += [f"| {k} | {v:,} |" for k, v in p["item_category_counts"].items()]
        lines.append("")
    if "events_per_year" in p:
        lines += ["## Events per year", "", "| Year | Events |", "| --- | --- |"]
        lines += [f"| {k} | {v:,} |" for k, v in p["events_per_year"].items()]
        lines.append("")
    lines += ["## Activities", "", "| Activity | Events |", "| --- | --- |"]
    lines += [f"| {k} | {v:,} |" for k, v in p["activity_counts"].items()]
    lines += ["", "## Events per case", ""]
    lines += [f"- {k}: {v:,.1f}" for k, v in p["events_per_case"].items()]
    lines += ["", "## Attributes found", "", "Case: " + ", ".join(p["case_attributes"]), "",
              "Event: " + ", ".join(p["event_attributes"]), ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xes", type=Path, nargs="?", help="path to the BPI 2019 .xes / .xes.gz / .zip "
                    "(default: the first one found in data/raw/)")
    ap.add_argument("--no-parquet", action="store_true", help="skip writing the parquet tables")
    args = ap.parse_args()
    if args.xes is None:
        raw = DATA_DIR / "raw"
        found = sorted(p for p in raw.iterdir() if p.name.endswith((".xes", ".xes.gz", ".zip")))
        if not found:
            sys.exit(f"no .xes file in {raw}. Run: python data/scripts/download_bpi2019.py")
        args.xes = found[0]

    print(f"reading {args.xes} ...")
    cases, events = load(args.xes)
    p = profile(cases, events)

    prof_dir = DATA_DIR / "profile"
    prof_dir.mkdir(parents=True, exist_ok=True)
    (prof_dir / "bpi2019_profile.json").write_text(json.dumps(p, indent=2, default=str))
    (prof_dir / "bpi2019_profile.md").write_text(to_markdown(p))

    if not args.no_parquet:
        out = DATA_DIR / "interim"
        out.mkdir(parents=True, exist_ok=True)
        cases.to_parquet(out / "bpi2019_cases.parquet", index=False)
        events.to_parquet(out / "bpi2019_events.parquet", index=False)

    bad = [k for k, c in p["checks"].items() if not c["ok"]]
    print(f"profile written to {prof_dir}")
    if bad:
        print(f"WARNING: counts differ from published figures for: {', '.join(bad)}")
        sys.exit(1)
    print("all counts match the published figures")


if __name__ == "__main__":
    main()
