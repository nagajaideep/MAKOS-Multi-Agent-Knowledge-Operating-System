"""Loader tests on the XES format fixture (not real data, parser/loader test only)."""
import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from makos.data.load_bpi import build_tables, load, verify
from profile_bpi2019 import load as read_xes

from tests_fixtures import FIXTURE_WITH_OUTLIER


@pytest.fixture
def frames(tmp_path):
    p = tmp_path / "log.xes"
    p.write_text(FIXTURE_WITH_OUTLIER, encoding="utf-8")
    return read_xes(p)


def test_build_tables_shapes(frames):
    t = build_tables(*frames)
    assert len(t["vendors"]) == 1
    assert len(t["purchase_documents"]) == 1
    assert len(t["po_items"]) == 2
    assert len(t["events"]) == 4
    assert t["po_items"]["goods_receipt_required"].tolist() == [True, None]
    assert t["events"]["ts_outlier"].sum() == 1


@pytest.mark.postgres
def test_load_into_postgres(pg_url, frames):
    engine = create_engine(pg_url)
    counts = load(engine, *frames, truncate=True)
    assert counts == {"cases": 2, "purchase_documents": 1, "events": 4, "activities": 3,
                      "vendors": 1, "ts_outliers": 1}
    with engine.connect() as c:
        row = c.execute(text(
            "SELECT activity, net_worth_eur, row_version FROM events WHERE case_id='DOC1_00010' ORDER BY seq"
        )).all()
    assert row[0] == ("Create Purchase Order Item", 100, 1)
    assert verify(counts, {"cases": 2, "events": 4, "purchase_documents": 1, "activities": 3, "vendors": 1}) == []
    assert verify(counts, {"cases": 251_734}) == ["cases"]

    # reload is idempotent with --truncate
    assert load(engine, *frames, truncate=True)["events"] == 4
    engine.dispose()
