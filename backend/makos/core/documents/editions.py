"""A versioned policy document (one edition of one source).

Editions are declared in each domain pack's pack.yaml; `effective_from` is the
date the edition came into force and drives temporal reasoning.
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
    kind: str  # "manual" (numbered paragraphs) or "rules" (e.g. GFR "Rule NNN")
