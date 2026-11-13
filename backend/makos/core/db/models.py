"""Core tables, shared by every domain pack (Stage-I design):
users, tasks, agent_runs, documents, evidence, workflow_steps, audit_events.

Domain packs add their own business tables (see backend/domains/<pack>/models.py).
A task points at its business record with a generic `subject_ref`, so the core
never depends on a particular domain.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from makos.core.db.base import Base


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
    pack: Mapped[str] = mapped_column(String(32))  # which domain pack the task belongs to
    subject_ref: Mapped[str | None] = mapped_column(String(128))  # e.g. "po_item:4507000164_00010"
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
