"""The domain-pack contract: what every pack must declare."""

import pytest

from makos.core.packs import DOMAINS_DIR, list_packs, load_pack


def test_bpi_pack_loads():
    pack = load_pack("bpi_p2p")
    assert pack.title.startswith("Purchase-to-pay")
    assert {e.name for e in pack.entities} >= {"vendor", "po_item", "event"}
    assert pack.raw_dir.name == "policy"
    assert pack.policy_map.exists()
    hold = next(a for a in pack.actions if a.name == "hold_invoice")
    assert hold.requires_approval and hold.allowed_roles == ("approver",)
    assert len(pack.editions) == 4


def test_list_packs_finds_bpi():
    assert "bpi_p2p" in list_packs()


def test_pack_models_register_tables():
    from makos.core.db.base import Base
    import makos.core.db.models  # noqa: F401

    load_pack("bpi_p2p").load_models()
    assert {"tasks", "audit_events", "po_items", "events"} <= set(Base.metadata.tables)


def test_core_tables_do_not_reference_pack_tables():
    from makos.core.db import models

    for table in models.Base.metadata.sorted_tables:
        if table.name in {"users", "tasks", "agent_runs", "documents", "evidence", "workflow_steps", "audit_events"}:
            for fk in table.foreign_keys:
                assert fk.column.table.name in {"users", "tasks", "agent_runs"}, (table.name, fk)


def _make_pack(tmp_path, body):
    d = tmp_path / "demo"
    d.mkdir()
    (d / "pack.yaml").write_text(body)
    return tmp_path


def test_missing_required_keys_rejected(tmp_path):
    root = _make_pack(tmp_path, "name: demo\ntitle: Demo\n")
    with pytest.raises(ValueError, match="missing keys"):
        load_pack("demo", root)


def test_name_must_match_folder(tmp_path):
    body = (DOMAINS_DIR / "bpi_p2p" / "pack.yaml").read_text().replace("name: bpi_p2p", "name: other")
    root = _make_pack(tmp_path, body)
    with pytest.raises(ValueError, match="declares name"):
        load_pack("demo", root)


def test_duplicate_edition_rejected(tmp_path):
    src = (DOMAINS_DIR / "bpi_p2p" / "pack.yaml").read_text().replace("name: bpi_p2p", "name: demo")
    src = src.replace('edition: "2022"', 'edition: "2017"')
    root = _make_pack(tmp_path, src)
    with pytest.raises(ValueError, match="same document edition"):
        load_pack("demo", root)
