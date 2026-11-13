"""Parser tests.

The XES snippet below is a hand-written FORMAT fixture used only to test the
parser. It is not data and is never used for evaluation.
"""
import gzip
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "data" / "scripts"))

from profile_bpi2019 import load, profile  # noqa: E402
from xes_reader import iter_traces  # noqa: E402

FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<log xes.version="1.0" xmlns="http://www.xes-standard.org/">
  <trace>
    <string key="concept:name" value="DOC1_00010"/>
    <string key="Purchasing Document" value="DOC1"/>
    <string key="Item Category" value="3-way match, invoice after GR"/>
    <string key="Vendor" value="vendorA"/>
    <boolean key="Goods Receipt" value="true"/>
    <event>
      <string key="concept:name" value="Create Purchase Order Item"/>
      <date key="time:timestamp" value="2018-01-02T10:00:00.000+01:00"/>
      <float key="Cumulative net worth (EUR)" value="100.0"/>
    </event>
    <event>
      <string key="concept:name" value="Record Goods Receipt"/>
      <date key="time:timestamp" value="2018-01-05T10:00:00.000+01:00"/>
      <float key="Cumulative net worth (EUR)" value="100.0"/>
    </event>
  </trace>
  <trace>
    <string key="concept:name" value="DOC1_00020"/>
    <string key="Purchasing Document" value="DOC1"/>
    <string key="Item Category" value="2-way match"/>
    <string key="Vendor" value="vendorA"/>
    <event>
      <string key="concept:name" value="Create Purchase Order Item"/>
      <date key="time:timestamp" value="2018-02-01T09:00:00.000+01:00"/>
    </event>
  </trace>
</log>
"""


def write_fixture(tmp_path, gz=False):
    path = tmp_path / ("log.xes.gz" if gz else "log.xes")
    if gz:
        with gzip.open(path, "wt", encoding="utf-8") as f:
            f.write(FIXTURE)
    else:
        path.write_text(FIXTURE, encoding="utf-8")
    return path


def test_iter_traces_reads_case_and_event_attributes(tmp_path):
    traces = list(iter_traces(write_fixture(tmp_path)))
    assert len(traces) == 2
    case, events = traces[0]
    assert case["Purchasing Document"] == "DOC1"
    assert case["Goods Receipt"] is True
    assert [e["concept:name"] for e in events] == ["Create Purchase Order Item", "Record Goods Receipt"]
    assert events[0]["Cumulative net worth (EUR)"] == 100.0


def test_gzip_input(tmp_path):
    assert len(list(iter_traces(write_fixture(tmp_path, gz=True)))) == 2


def test_profile_counts(tmp_path):
    cases, events = load(write_fixture(tmp_path))
    p = profile(cases, events)
    assert p["cases"] == 2
    assert p["events"] == 3
    assert p["purchase_documents"] == 1
    assert p["activities"] == 2
    assert p["item_category_counts"]["2-way match"] == 1
    assert p["checks"]["cases"]["ok"] is False  # fixture is not the real log
