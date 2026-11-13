"""Baseline audit of BPI 2019 PO line items (stage 4).

Plain pandas checks built from the matching rules in the BPI 2019 dataset
description. They give us:

* candidate labels for every case (to be checked by two human reviewers), and
* the non-agent baseline that the KRN engine and agents must beat or match.

Codes (numbering follows the KRN rules in the plan):

  R1  VALUE_MISMATCH   3-way item, invoice cleared, invoiced value != goods-receipt value
  R2  OVER_PO_VALUE    2-way item, invoiced value > PO value
  R3  IR_BEFORE_GR     "invoice after GR" item whose first invoice precedes its first goods receipt
  R4  PAID_WITHOUT_GR  3-way item, invoice cleared, no net goods receipt
  R6  DUPLICATE_IR     two invoice receipts with the same value within the window, not cancelled

R5 (invoice without PO) cannot occur at item level in BPI: every case is a PO item.
Consignment items are not invoiced per item and get no value checks.
Events flagged as timestamp outliers are ignored for ordering checks.

Tolerances are modelling choices; the evaluation reports sensitivity to them.

    python -m domains.bpi_p2p.audit
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from makos.config import DATA_DIR

THREE_WAY = {"3-way match, invoice before GR", "3-way match, invoice after GR"}
AFTER_GR = "3-way match, invoice after GR"
TWO_WAY = "2-way match"

PO_VALUE_EVENTS = {"Create Purchase Order Item", "Change Price", "Change Quantity"}
GR_PLUS, GR_MINUS = {"Record Goods Receipt"}, {"Cancel Goods Receipt"}
IR_PLUS = {"Record Invoice Receipt", "Record Subsequent Invoice"}
IR_MINUS = {"Cancel Invoice Receipt", "Cancel Subsequent Invoice"}
CLEAR = "Clear Invoice"

VALUE_COL = "Cumulative net worth (EUR)"
TS_COL = "time:timestamp"


@dataclass(frozen=True)
class AuditConfig:
    rel_tol: float = 0.01        # 1% relative tolerance on value matches
    abs_tol: float = 1.0         # and at least 1 EUR (amounts are linearly anonymized)
    dup_window_days: int = 14
    valid_from: str = "2017-01-01"
    valid_to: str = "2020-01-01"


def _mismatch(a: pd.Series, b: pd.Series, cfg: AuditConfig) -> pd.Series:
    limit = (pd.concat([a.abs(), b.abs()], axis=1).max(axis=1) * cfg.rel_tol).clip(lower=cfg.abs_tol)
    return (a - b).abs() > limit


def case_facts(cases: pd.DataFrame, events: pd.DataFrame, cfg: AuditConfig = AuditConfig()) -> pd.DataFrame:
    """One row per case with the facts the checks need."""
    ev = events[["case_id", "seq", "activity", TS_COL, VALUE_COL]].copy()
    ev[TS_COL] = pd.to_datetime(ev[TS_COL], utc=True, errors="coerce")
    ev[VALUE_COL] = pd.to_numeric(ev[VALUE_COL], errors="coerce").fillna(0.0)
    ok_ts = ev[TS_COL].between(pd.Timestamp(cfg.valid_from, tz="UTC"),
                               pd.Timestamp(cfg.valid_to, tz="UTC"), inclusive="left")

    def signed(plus: set, minus: set) -> pd.Series:
        sign = ev["activity"].map(lambda a: 1 if a in plus else (-1 if a in minus else 0))
        return (ev[VALUE_COL] * sign).groupby(ev["case_id"]).sum()

    po_ev = ev[ev["activity"].isin(PO_VALUE_EVENTS)].sort_values(["case_id", "seq"])
    facts = pd.DataFrame(index=cases["case_id"])
    facts["po_value"] = po_ev.groupby("case_id")[VALUE_COL].last()
    facts["gr_total"] = signed(GR_PLUS, GR_MINUS)
    facts["ir_total"] = signed(IR_PLUS, IR_MINUS)
    facts["n_ir"] = ev[ev["activity"].isin(IR_PLUS)].groupby("case_id").size()
    facts["cleared"] = ev[ev["activity"] == CLEAR].groupby("case_id").size() > 0
    timed = ev[ok_ts]
    facts["first_gr_ts"] = timed[timed["activity"].isin(GR_PLUS)].groupby("case_id")[TS_COL].min()
    facts["first_ir_ts"] = timed[timed["activity"].isin(IR_PLUS)].groupby("case_id")[TS_COL].min()
    facts["dup_ir"] = _duplicate_invoices(ev, cfg)
    facts = facts.fillna({"gr_total": 0.0, "ir_total": 0.0, "n_ir": 0, "cleared": False, "dup_ir": False})
    facts["item_category"] = cases.set_index("case_id")["Item Category"]
    return facts.reset_index().rename(columns={"index": "case_id"})


def _duplicate_invoices(ev: pd.DataFrame, cfg: AuditConfig) -> pd.Series:
    ir = ev[ev["activity"] == "Record Invoice Receipt"].sort_values(["case_id", TS_COL])
    cancels = ev[ev["activity"] == "Cancel Invoice Receipt"]
    cancelled = set(zip(cancels["case_id"], cancels[VALUE_COL].round(2)))
    ir = ir.assign(v=ir[VALUE_COL].round(2))
    ir["prev_v"] = ir.groupby("case_id")["v"].shift()
    ir["gap"] = ir.groupby("case_id")[TS_COL].diff()
    hit = (ir["v"] == ir["prev_v"]) & (ir["v"] != 0) & (ir["gap"] <= pd.Timedelta(days=cfg.dup_window_days))
    hit &= ~pd.Series([(c, v) in cancelled for c, v in zip(ir["case_id"], ir["v"])], index=ir.index)
    return hit.groupby(ir["case_id"]).any()


def apply_checks(facts: pd.DataFrame, cfg: AuditConfig = AuditConfig()) -> pd.DataFrame:
    f = facts
    cat = f["item_category"]
    out = pd.DataFrame({"case_id": f["case_id"], "item_category": cat})
    out["R1_VALUE_MISMATCH"] = (cat.isin(THREE_WAY) & f["cleared"] & (f["gr_total"] > 0) & (f["ir_total"] > 0)
                                & _mismatch(f["ir_total"], f["gr_total"], cfg))
    out["R2_OVER_PO_VALUE"] = ((cat == TWO_WAY) & f["po_value"].notna() & (f["ir_total"] > 0)
                               & (f["ir_total"] > f["po_value"] * (1 + cfg.rel_tol) + cfg.abs_tol))
    out["R3_IR_BEFORE_GR"] = ((cat == AFTER_GR) & f["first_ir_ts"].notna()
                              & (f["first_gr_ts"].isna() | (f["first_ir_ts"] < f["first_gr_ts"])))
    out["R4_PAID_WITHOUT_GR"] = cat.isin(THREE_WAY) & f["cleared"] & (f["gr_total"] <= 0)
    out["R6_DUPLICATE_IR"] = (cat != "Consignment") & f["dup_ir"].astype(bool)
    codes = [c for c in out.columns if c.startswith("R")]
    out["n_exceptions"] = out[codes].sum(axis=1)
    out["candidate_label"] = out["n_exceptions"].map(lambda n: "exception" if n else "no_exception")
    return out


def split_for(po_id: str, salt: str = "makos-2026") -> str:
    """Deterministic 60/20/20 split by purchase document (no PO spans two splits)."""
    bucket = int(hashlib.sha256(f"{salt}:{po_id}".encode()).hexdigest(), 16) % 100
    return "train" if bucket < 60 else ("val" if bucket < 80 else "test")


def summarize(labels: pd.DataFrame, cfg: AuditConfig) -> dict:
    codes = [c for c in labels.columns if c.startswith("R")]
    by_cat = labels.groupby("item_category")[codes].sum().astype(int)
    return {
        "config": asdict(cfg),
        "cases": int(len(labels)),
        "cases_with_exception": int((labels["n_exceptions"] > 0).sum()),
        "per_rule": {c: int(labels[c].sum()) for c in codes},
        "per_rule_by_category": by_cat.to_dict(orient="index"),
        "split_cases": labels["split"].value_counts().to_dict(),
        "split_exception_rate": labels.groupby("split")["n_exceptions"].apply(lambda s: round(float((s > 0).mean()), 4)).to_dict(),
    }


def to_markdown(s: dict) -> str:
    lines = ["# BPI 2019: baseline audit (candidate labels)", "",
             "Rule-derived **candidate** labels. They are not ground truth until the two-reviewer check (stage 18).", "",
             f"Config: `{json.dumps(s['config'])}`", "",
             f"- Cases audited: {s['cases']:,}",
             f"- Cases with at least one candidate exception: {s['cases_with_exception']:,} "
             f"({s['cases_with_exception'] / max(s['cases'], 1):.1%})", "",
             "| Rule | Cases flagged |", "| --- | --- |"]
    lines += [f"| {k} | {v:,} |" for k, v in s["per_rule"].items()]
    rules = list(s["per_rule"])
    lines += ["", "## By item category", "", "| Category | " + " | ".join(rules) + " |",
              "| --- |" + " --- |" * len(rules)]
    for cat, row in s["per_rule_by_category"].items():
        lines.append(f"| {cat} | " + " | ".join(f"{row[r]:,}" for r in rules) + " |")
    lines += ["", "## Splits (by purchase document)", "", "| Split | Cases | Exception rate |", "| --- | --- | --- |"]
    for k in ("train", "val", "test"):
        if k in s["split_cases"]:
            lines.append(f"| {k} | {s['split_cases'][k]:,} | {s['split_exception_rate'][k]:.1%} |")
    return "\n".join(lines) + "\n"


def run(cases: pd.DataFrame, events: pd.DataFrame, cfg: AuditConfig = AuditConfig()) -> tuple[pd.DataFrame, dict]:
    facts = case_facts(cases, events, cfg)
    labels = apply_checks(facts, cfg)
    po = cases.set_index("case_id")["Purchasing Document"]
    labels["po_id"] = labels["case_id"].map(po)
    labels["split"] = labels["po_id"].map(split_for)
    labels = labels.merge(facts.drop(columns=["item_category"]), on="case_id")
    return labels, summarize(labels, cfg)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rel-tol", type=float, default=AuditConfig.rel_tol)
    args = ap.parse_args()
    cfg = AuditConfig(rel_tol=args.rel_tol)

    interim = DATA_DIR / "interim"
    print("reading parquet ...")
    cases = pd.read_parquet(interim / "bpi2019_cases.parquet")
    events = pd.read_parquet(interim / "bpi2019_events.parquet")
    labels, summary = run(cases, events, cfg)

    out_dir = DATA_DIR / "labels"
    out_dir.mkdir(parents=True, exist_ok=True)
    labels.to_parquet(out_dir / "candidate_labels.parquet", index=False)
    splits_dir = DATA_DIR / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)
    labels[["po_id", "split"]].drop_duplicates().sort_values("po_id").to_csv(splits_dir / "bpi2019_po_splits.csv", index=False)
    prof = DATA_DIR / "profile"
    (prof / "baseline_audit.json").write_text(json.dumps(summary, indent=2, default=str))
    (prof / "baseline_audit.md").write_text(to_markdown(summary))
    print(to_markdown(summary))


if __name__ == "__main__":
    main()
