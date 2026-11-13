"""BPI Challenge 2019 business tables (real purchase-to-pay records).

Rows carry `row_version` so the Cross-Context Layer can tell when data it
depended on has changed.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from makos.core.db.base import Base


class Vendor(Base):
    __tablename__ = "vendors"
    vendor_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(128))


class PurchaseDocument(Base):
    __tablename__ = "purchase_documents"
    po_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    vendor_id: Mapped[str | None] = mapped_column(ForeignKey("vendors.vendor_id"))
    company: Mapped[str | None] = mapped_column(String(64))
    document_type: Mapped[str | None] = mapped_column(String(64))
    category_name: Mapped[str | None] = mapped_column(String(64))
    source_system: Mapped[str | None] = mapped_column(String(64))


class POItem(Base):
    """One BPI case = one purchase-order line item."""

    __tablename__ = "po_items"
    case_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    po_id: Mapped[str] = mapped_column(ForeignKey("purchase_documents.po_id"), index=True)
    item: Mapped[str | None] = mapped_column(String(16))
    item_type: Mapped[str | None] = mapped_column(String(64))
    item_category: Mapped[str] = mapped_column(String(64), index=True)
    gr_based_inv_verif: Mapped[bool | None] = mapped_column(Boolean)
    goods_receipt_required: Mapped[bool | None] = mapped_column(Boolean)
    spend_area: Mapped[str | None] = mapped_column(String(128))
    sub_spend_area: Mapped[str | None] = mapped_column(String(128))
    spend_classification: Mapped[str | None] = mapped_column(String(128))
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")


class Event(Base):
    __tablename__ = "events"
    event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("po_items.case_id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    activity: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ts_outlier: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    user_name: Mapped[str | None] = mapped_column(String(64))
    org_resource: Mapped[str | None] = mapped_column(String(64))
    net_worth_eur: Mapped[float | None] = mapped_column(Numeric(18, 2))
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    __table_args__ = (Index("ix_events_case_seq", "case_id", "seq", unique=True),)
