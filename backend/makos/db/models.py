"""Database schema.

Two groups of tables:

* Business data loaded from BPI Challenge 2019 (real records): vendors,
  purchase_documents, po_items, events. Rows carry `row_version` so the
  Cross-Context Layer can tell when data it depended on has changed.
* Application state from the Stage-I design: users, tasks, agent_runs,
  documents, evidence, workflow_steps, audit_events.
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
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------- business data


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


# ------------------------------------------------------------ application state


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    role: Mapped[str] = mapped_column(String(16))  # analyst | approver | admin
    department: Mapped[str | None] = mapped_column(String(64))


class Task(Base):
    __tablename__ = "tasks"
    task_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    intent: Mapped[str] = mapped_column(String(64))
    request_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), server_default="open")
    case_ref: Mapped[str | None] = mapped_column(ForeignKey("po_items.case_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentRun(Base):
    __tablename__ = "agent_runs"
    run_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.task_id"), index=True)
    agent_type: Mapped[str] = mapped_column(String(32))
    input_hash: Mapped[str] = mapped_column(String(64))
    output: Mapped[dict | None] = mapped_column(JSONB)
    tools_called: Mapped[list | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    tokens: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Document(Base):
    __tablename__ = "documents"
    document_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64))  # e.g. goods_manual
    edition: Mapped[str] = mapped_column(String(32))  # e.g. 2017, 2022-update, 2024
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    uri: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(String(64))


class Evidence(Base):
    __tablename__ = "evidence"
    evidence_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.task_id"), index=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("agent_runs.run_id"))
    kind: Mapped[str] = mapped_column(String(16))  # clause | record | rule
    source_ref: Mapped[str] = mapped_column(Text)  # clause id or table:row
    excerpt: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Numeric(6, 4))


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    step_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.task_id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(64))
    approval_state: Mapped[str] = mapped_column(String(16), server_default="none")
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True)


class AuditEvent(Base):
    """Append-only; each row stores the hash of the previous one (hash chain)."""

    __tablename__ = "audit_events"
    event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.task_id"), index=True)
    actor: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict | None] = mapped_column(JSONB)
    prev_hash: Mapped[str | None] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
