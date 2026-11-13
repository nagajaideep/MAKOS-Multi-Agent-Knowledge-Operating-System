"""Unit tests for the baseline checks. Inputs are hand-built test cases, not data."""
import pandas as pd

from makos.audit.baseline import AuditConfig, run, split_for

AFTER = "3-way match, invoice after GR"
BEFORE = "3-way match, invoice before GR"


def make(cases_spec):
    """cases_spec: {case_id: (category, [(activity, 'YYYY-MM-DD', value), ...])}"""
    cases, events = [], []
    for cid, (cat, evs) in cases_spec.items():
        cases.append({"case_id": cid, "Item Category": cat, "Purchasing Document": cid.split("_")[0]})
        for seq, (act, day, val) in enumerate(evs):
            events.append({"case_id": cid, "seq": seq, "activity": act,
                           "time:timestamp": f"{day}T10:00:00+00:00", "Cumulative net worth (EUR)": val})
    return pd.DataFrame(cases), pd.DataFrame(events)


SPEC = {
    # clean 3-way: GR then IR, equal values, cleared
    "P1_1": (AFTER, [("Create Purchase Order Item", "2018-01-01", 100), ("Record Goods Receipt", "2018-01-05", 100),
                     ("Record Invoice Receipt", "2018-01-06", 100), ("Clear Invoice", "2018-02-01", 100)]),
    # R1: invoiced 150 vs received 100
    "P2_1": (BEFORE, [("Create Purchase Order Item", "2018-01-01", 100), ("Record Invoice Receipt", "2018-01-02", 150),
                      ("Record Goods Receipt", "2018-01-05", 100), ("Clear Invoice", "2018-02-01", 150)]),
    # within tolerance: 100.5 vs 100 -> no R1
    "P3_1": (BEFORE, [("Record Goods Receipt", "2018-01-05", 100), ("Record Invoice Receipt", "2018-01-06", 100.5),
                      ("Clear Invoice", "2018-02-01", 100.5)]),
    # R2: 2-way invoice above PO value
    "P4_1": ("2-way match", [("Create Purchase Order Item", "2018-01-01", 100), ("Record Invoice Receipt", "2018-01-03", 130)]),
    # 2-way after a price change to 130 -> no R2
    "P5_1": ("2-way match", [("Create Purchase Order Item", "2018-01-01", 100), ("Change Price", "2018-01-02", 130),
                             ("Record Invoice Receipt", "2018-01-03", 130)]),
    # R3: invoice-after-GR item invoiced first
    "P6_1": (AFTER, [("Record Invoice Receipt", "2018-01-02", 100), ("Record Goods Receipt", "2018-01-05", 100)]),
    # R3 ignored when the early invoice has an outlier timestamp (1948)
    "P7_1": (AFTER, [("Record Invoice Receipt", "1948-01-27", 100), ("Record Goods Receipt", "2018-01-05", 100)]),
    # R4: cleared, goods receipt cancelled to zero
    "P8_1": (BEFORE, [("Record Goods Receipt", "2018-01-05", 100), ("Cancel Goods Receipt", "2018-01-06", 100),
                      ("Record Invoice Receipt", "2018-01-07", 100), ("Clear Invoice", "2018-02-01", 100)]),
    # R6: same invoice value twice within 14 days
    "P9_1": (BEFORE, [("Record Invoice Receipt", "2018-03-01", 80), ("Record Invoice Receipt", "2018-03-05", 80)]),
    # same value twice but one was cancelled -> no R6
    "P10_1": (BEFORE, [("Record Invoice Receipt", "2018-03-01", 80), ("Cancel Invoice Receipt", "2018-03-02", 80),
                       ("Record Invoice Receipt", "2018-03-05", 80)]),
    # consignment never gets value checks
    "P11_1": ("Consignment", [("Create Purchase Order Item", "2018-01-01", 0), ("Record Goods Receipt", "2018-01-05", 0)]),
}


def labels():
    lab, summary = run(*make(SPEC), AuditConfig())
    return lab.set_index("case_id"), summary


def flagged(lab, rule):
    return set(lab.index[lab[rule]])


def test_each_rule_fires_only_where_expected():
    lab, _ = labels()
    assert flagged(lab, "R1_VALUE_MISMATCH") == {"P2_1"}
    assert flagged(lab, "R2_OVER_PO_VALUE") == {"P4_1"}
    assert flagged(lab, "R3_IR_BEFORE_GR") == {"P6_1"}
    assert flagged(lab, "R4_PAID_WITHOUT_GR") == {"P8_1"}
    assert flagged(lab, "R6_DUPLICATE_IR") == {"P9_1"}


def test_clean_cases_have_no_exception():
    lab, _ = labels()
    for cid in ["P1_1", "P3_1", "P5_1", "P7_1", "P10_1", "P11_1"]:
        assert lab.loc[cid, "candidate_label"] == "no_exception", cid


def test_summary_counts():
    _, s = labels()
    assert s["cases"] == len(SPEC)
    assert s["cases_with_exception"] == 5


def test_split_is_deterministic_and_balanced():
    assert split_for("4507000164") == split_for("4507000164")
    splits = pd.Series([split_for(str(i)) for i in range(20_000)]).value_counts(normalize=True)
    assert abs(splits["train"] - 0.6) < 0.02 and abs(splits["test"] - 0.2) < 0.02
