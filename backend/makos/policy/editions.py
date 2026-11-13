"""Policy documents and their editions (see data/REGISTER.md).

`effective_from` is the date an edition came into force for our temporal
reasoning: 2017 = foreword date, 2022 = public release, 2024 = covering OM.
`sha256` is filled once a file has been checked by the team; None = not yet.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Edition:
    source_id: str
    edition: str
    title: str
    effective_from: date
    filename: str
    url: str
    sha256: str | None
    kind: str  # "manual" (numbered paragraphs) or "gfr" (Rule NNN)


EDITIONS: list[Edition] = [
    Edition(
        "goods_manual", "2017", "Manual for Procurement of Goods, 2017", date(2017, 4, 5),
        "Manual_for_Procurement_of_Goods_2017.pdf",
        "https://ns1.sctimst.ac.in/About%20SCTIMST/Right%20to%20Information/resources/"
        "Manual%20for%20Procurement%20of%20Goods%202017.pdf",
        "9d4d7179170aea9effcec3d134e98c53785db548cd1b8b18b5e7ce6836621f9f", "manual",
    ),
    Edition(
        "goods_manual", "2022", "Manual for Procurement of Goods (Updated June, 2022)", date(2022, 7, 1),
        "Manual_for_Procurement_of_Goods_2022.pdf",
        "https://sric.iitkgp.ac.in/web4/public/docss/Manual%20for%20Procurement%20of%20Goods.pdf",
        "ac9e31c465496bccfd2aa221773645bf1edaa0786b1911ddd136bffa09d79b2b", "manual",
    ),
    Edition(
        "goods_manual", "2024", "Manual for Procurement of Goods, Second Edition, 2024", date(2024, 8, 16),
        "Manual_for_Procurement_of_Goods_2024.pdf",
        "https://doe.gov.in/manuals",  # official listing page; download the 2024 Goods manual from it
        "351b1f6f4cde096e5be83a9e331ca0fa25c0ceda91596c2b4db6a028aaef3b4c", "manual",
    ),
    Edition(
        "gfr", "2017-amended-2024-07-31", "General Financial Rules 2017, Ch. 6 (amended up to 31.07.2024)",
        date(2024, 7, 31),
        "GFR_2017_Amended_upto_31-07-2024.pdf",
        "https://iitk.ac.in/centralstores/data/GFR_2017_Amended_upto_31-07-2024.pdf",
        "be7bad84362c4ddb305f5cb8c800bd112bec613f4320097f69ec49ed85f0c87b", "gfr",
    ),
]


def in_force(source_id: str, on: date) -> Edition | None:
    """The edition of `source_id` in force on a date (latest effective_from <= on)."""
    candidates = [e for e in EDITIONS if e.source_id == source_id and e.effective_from <= on]
    return max(candidates, key=lambda e: e.effective_from) if candidates else None
