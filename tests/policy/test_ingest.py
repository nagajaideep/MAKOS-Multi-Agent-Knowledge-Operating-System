"""Parser tests on hand-written page text (format fixtures, not policy data)."""
from datetime import date

from makos.core.documents.editions import Edition
from makos.core.documents.ingest import parse_manual, parse_rules
from makos.core.packs import load_pack

ED = Edition("goods_manual", "test", "Test manual", date(2020, 1, 1), "t.pdf", "", None, "manual")

TOC = """Table of Contents
1.1 Procurement Rules 1
1.2 Clarification 1
2.1 Need Assessment 27
9.14 Accounting and Payment 169
10.1 Scrap for Disposal 172"""

BODY_1 = """Chapter 1: Introduction
1.1 Procurement Rules and Regulations
The rules apply to all purchases. Amounts like
2.5 lakh rupees must not be read as headings.
12
1.2 Clarification and Amendments
Text of 1.2."""

BODY_2 = """Chapter 9: Contract Management
9.14 Accounting and Payment of Received Materials
9.14.1 Goods Receipt and Inspection Report
If the received material passes checks, a GRIR is prepared.
9.14.2 Passing of Supplier's Bills
After the GRIR is issued, the invoice is received. Payment follows
Annexure 22 shows the GRIR form."""

ANNEX = """Annexure 1
Delegation of financial powers
1.1 this must not become a clause"""


def test_manual_parser_skips_toc_and_stops_at_annexures():
    clauses = parse_manual([TOC, BODY_1, BODY_2, ANNEX], ED)
    numbers = [c.number for c in clauses]
    assert numbers == ["1.1", "1.2", "9.14", "9.14.1", "9.14.2"]
    by = {c.number: c for c in clauses}
    assert "2.5 lakh" in by["1.1"].text          # not split into a fake heading
    assert by["9.14.1"].title == "Goods Receipt and Inspection Report"
    assert by["9.14.1"].parent_title == "Accounting and Payment of Received Materials"
    assert by["9.14.2"].page_start == 3
    assert "Annexure 22" in by["9.14.2"].text    # in-text mention does not stop parsing
    assert by["9.14.2"].clause_id == "goods_manual:test:9.14.2"


def test_sentence_heading_is_not_a_title():
    page = "1.1 Public procurement is perceived to be prone to corruption and ethical risks. To\nmore text"
    c = parse_manual([page], ED)[0]
    assert c.title == ""
    assert c.text.startswith("Public procurement")


def test_gfr_rules_with_repeated_numbers_get_unique_ids():
    gfr = Edition("gfr", "x", "GFR", date(2024, 7, 31), "g.pdf", "", None, "rules")
    page = "Rule 151 Debarment from bidding.\n(i) text\nRule 172 (1) Advance payment\nRule 172 (2) Part payment"
    ids = [c.clause_id for c in parse_rules([page], gfr)]
    assert ids == ["gfr:x:Rule 151", "gfr:x:Rule 172", "gfr:x:Rule 172 (part 2)"]


def test_edition_in_force_on_date():
    pack = load_pack("bpi_p2p")
    assert pack.edition_in_force("goods_manual", date(2018, 6, 1)).edition == "2017"
    assert pack.edition_in_force("goods_manual", date(2023, 1, 1)).edition == "2022"
    assert pack.edition_in_force("goods_manual", date(2025, 1, 1)).edition == "2024"
    assert pack.edition_in_force("goods_manual", date(2016, 1, 1)) is None
