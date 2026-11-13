"""Domain packs: how a use case plugs into the MAKOS core.

A pack is a folder `backend/domains/<name>/` with a `pack.yaml` describing
what is domain specific: business entities and their join keys, the policy
documents and their versions, the policy map, the actions agents may propose,
and the evaluation sets. The core (orchestrator, Cross-Context Layer, agents,
retrieval, rule engine, approvals, audit) reads only this contract and never
imports a pack's code by name.

    from makos.core.packs import load_pack, list_packs
    pack = load_pack("bpi_p2p")
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from makos.config import ROOT
from makos.core.documents.editions import Edition

DOMAINS_DIR = ROOT / "backend" / "domains"
REQUIRED_KEYS = {"name", "title", "description", "entities", "documents", "actions"}


@dataclass(frozen=True)
class Entity:
    name: str          # e.g. "po_item"
    table: str         # database table
    key: str           # join key column, e.g. "case_id" or "recipient_uei"
    description: str = ""


@dataclass(frozen=True)
class Action:
    name: str                  # e.g. "hold_invoice"
    description: str
    requires_approval: bool    # sensitive actions go through the approval gate
    allowed_roles: tuple[str, ...]


@dataclass
class DomainPack:
    name: str
    title: str
    description: str
    root: Path
    entities: list[Entity]
    editions: list[Edition]
    raw_dir: Path
    actions: list[Action]
    policy_map: Path | None = None
    models_module: str | None = None
    eval_sets: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def edition_in_force(self, source_id: str, on: date) -> Edition | None:
        """The edition of a document in force on a date (latest effective_from <= on)."""
        candidates = [e for e in self.editions if e.source_id == source_id and e.effective_from <= on]
        return max(candidates, key=lambda e: e.effective_from) if candidates else None

    def load_models(self) -> None:
        """Import the pack's table definitions so they register on the shared Base."""
        if self.models_module:
            importlib.import_module(self.models_module)


def _edition(src: dict, ed: dict) -> Edition:
    return Edition(
        source_id=src["source_id"], edition=str(ed["edition"]), title=ed["title"],
        effective_from=date.fromisoformat(str(ed["effective_from"])), filename=ed["filename"],
        url=ed.get("url", ""), sha256=ed.get("sha256"), kind=src.get("kind", "manual"),
    )


def load_pack(name: str, domains_dir: Path = DOMAINS_DIR) -> DomainPack:
    root = domains_dir / name
    spec_path = root / "pack.yaml"
    if not spec_path.exists():
        raise FileNotFoundError(f"no pack.yaml for domain pack '{name}' in {root}")
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    missing = REQUIRED_KEYS - spec.keys()
    if missing:
        raise ValueError(f"pack '{name}' is missing keys: {sorted(missing)}")
    if spec["name"] != name:
        raise ValueError(f"pack folder '{name}' declares name '{spec['name']}'")

    editions = [_edition(src, ed) for src in spec["documents"].get("sources", []) for ed in src["editions"]]
    keys = [(e.source_id, e.edition) for e in editions]
    if len(keys) != len(set(keys)):
        raise ValueError(f"pack '{name}' lists the same document edition twice")

    return DomainPack(
        name=name,
        title=spec["title"],
        description=spec["description"],
        root=root,
        entities=[Entity(**e) for e in spec["entities"]],
        editions=editions,
        raw_dir=ROOT / spec["documents"].get("raw_dir", f"data/raw/{name}"),
        actions=[Action(name=a["name"], description=a["description"],
                        requires_approval=bool(a.get("requires_approval", True)),
                        allowed_roles=tuple(a.get("allowed_roles", ["approver"])))
                 for a in spec["actions"]],
        policy_map=(root / spec["policy_map"]) if spec.get("policy_map") else None,
        models_module=spec.get("models_module"),
        eval_sets=spec.get("eval_sets", {}),
        extra={k: v for k, v in spec.items() if k not in REQUIRED_KEYS | {
            "policy_map", "models_module", "eval_sets"}},
    )


def list_packs(domains_dir: Path = DOMAINS_DIR) -> list[str]:
    return sorted(p.parent.name for p in domains_dir.glob("*/pack.yaml"))
