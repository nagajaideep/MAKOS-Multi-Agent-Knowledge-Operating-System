"""Load BPI Challenge 2019 into PostgreSQL.

Reads the parquet tables written by data/scripts/profile_bpi2019.py and bulk
loads them with COPY. Then checks the database counts against
data/profile/bpi2019_profile.json.

    alembic upgrade head
    python -m makos.data.load_bpi            # add --truncate to reload
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from makos.config import DATA_DIR
from makos.db.session import get_engine

INTERIM = DATA_DIR / "interim"
PROFILE = DATA_DIR / "profile" / "bpi2019_profile.json"

# Events outside this window are kept but flagged (see data/REGISTER.md).
VALID_FROM = pd.Timestamp("2017-01-01", tz="UTC")
VALID_TO = pd.Timestamp("2020-01-01", tz="UTC")

TABLES = ["events", "po_items", "purchase_documents", "vendors"]


def _clean(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if v is pd.NaT:
        return None
    return v


def _bool(v):
    v = _clean(v)
    if v is None:
        return None
    if isinstance(v, str):
        return v.strip().lower() == "true"
    return bool(v)


def build_tables(cases: pd.DataFrame, events: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Turn the raw BPI case/event frames into rows for each table."""
    vendors = (
        cases.reindex(columns=["Vendor", "Name"])
        .dropna(subset=["Vendor"])
        .drop_duplicates("Vendor")
        .rename(columns={"Vendor": "vendor_id", "Name": "name"})
    )
    docs = (
        cases.sort_values("case_id")
        .drop_duplicates("Purchasing Document")
        .rename(columns={
            "Purchasing Document": "po_id",
            "Vendor": "vendor_id",
            "Company": "company",
            "Document Type": "document_type",
            "Purch. Doc. Category name": "category_name",
            "Source": "source_system",
        }).reindex(columns=["po_id", "vendor_id", "company", "document_type", "category_name", "source_system"])
    )
    items = cases.rename(columns={
        "Purchasing Document": "po_id",
        "Item": "item",
        "Item Type": "item_type",
        "Item Category": "item_category",
        "GR-Based Inv. Verif.": "gr_based_inv_verif",
        "Goods Receipt": "goods_receipt_required",
        "Spend area text": "spend_area",
        "Sub spend area text": "sub_spend_area",
        "Spend classification text": "spend_classification",
    }).reindex(columns=["case_id", "po_id", "item", "item_type", "item_category", "gr_based_inv_verif",
                        "goods_receipt_required", "spend_area", "sub_spend_area", "spend_classification"])
    for col in ("gr_based_inv_verif", "goods_receipt_required"):
        items[col] = items[col].map(_bool)

    ts = pd.to_datetime(events["time:timestamp"], utc=True, errors="coerce")
    ev = pd.DataFrame({
        "case_id": events["case_id"],
        "seq": events["seq"].astype(int),
        "activity": events["activity"],
        "ts": ts,
        "ts_outlier": (ts < VALID_FROM) | (ts >= VALID_TO),
        "user_name": events.get("User"),
        "org_resource": events.get("org:resource"),
        "net_worth_eur": events.get("Cumulative net worth (EUR)"),
    })
    return {"vendors": vendors, "purchase_documents": docs, "po_items": items, "events": ev}


def copy_rows(engine: Engine, table: str, df: pd.DataFrame) -> None:
    cols = list(df.columns)
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cur:
            with cur.copy(f"COPY {table} ({', '.join(cols)}) FROM STDIN") as cp:
                for row in df.itertuples(index=False, name=None):
                    cp.write_row([_clean(v) for v in row])
        raw.commit()
    finally:
        raw.close()


def load(engine: Engine, cases: pd.DataFrame, events: pd.DataFrame, truncate: bool = False) -> dict:
    tables = build_tables(cases, events)
    with engine.begin() as conn:
        if truncate:
            conn.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
    for name in ["vendors", "purchase_documents", "po_items", "events"]:
        print(f"  loading {name}: {len(tables[name]):,} rows")
        copy_rows(engine, name, tables[name])
    return db_counts(engine)


def db_counts(engine: Engine) -> dict:
    with engine.connect() as conn:
        return {
            "cases": conn.execute(text("SELECT count(*) FROM po_items")).scalar_one(),
            "purchase_documents": conn.execute(text("SELECT count(*) FROM purchase_documents")).scalar_one(),
            "events": conn.execute(text("SELECT count(*) FROM events")).scalar_one(),
            "activities": conn.execute(text("SELECT count(DISTINCT activity) FROM events")).scalar_one(),
            "vendors": conn.execute(text("SELECT count(*) FROM vendors")).scalar_one(),
            "ts_outliers": conn.execute(text("SELECT count(*) FROM events WHERE ts_outlier")).scalar_one(),
        }


def verify(counts: dict, profile: dict) -> list[str]:
    """Return the measures whose database count differs from the profile."""
    keys = ["cases", "purchase_documents", "events", "activities", "vendors"]
    return [k for k in keys if k in profile and counts.get(k) != profile[k]]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--truncate", action="store_true", help="empty the business tables first")
    ap.add_argument("--database-url", help="override MAKOS_DATABASE_URL")
    args = ap.parse_args()

    cases_path, events_path = INTERIM / "bpi2019_cases.parquet", INTERIM / "bpi2019_events.parquet"
    if not cases_path.exists():
        sys.exit("parquet files not found. Run: python data/scripts/profile_bpi2019.py")
    print("reading parquet ...")
    cases, events = pd.read_parquet(cases_path), pd.read_parquet(events_path)
    engine = get_engine(args.database_url)
    counts = load(engine, cases, events, truncate=args.truncate)
    print(json.dumps(counts, indent=2))

    bad = verify(counts, json.loads(PROFILE.read_text()))
    if bad:
        sys.exit(f"database counts differ from the profile for: {', '.join(bad)}")
    print("database counts match the profile")


if __name__ == "__main__":
    main()
