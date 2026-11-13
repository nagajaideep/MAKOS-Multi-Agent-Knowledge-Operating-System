"""Shared fixtures.

Database tests need PostgreSQL. Point MAKOS_TEST_DATABASE_URL at a server
where the user may create databases, e.g.
    postgresql+psycopg://makos:makos@localhost:5432/postgres
Each test session creates and drops its own database.
"""
import os
import sys
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data" / "scripts"))


@pytest.fixture(scope="session")
def pg_url():
    base = os.environ.get("MAKOS_TEST_DATABASE_URL")
    if not base:
        pytest.skip("MAKOS_TEST_DATABASE_URL not set")
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    name = f"makos_test_{uuid.uuid4().hex[:8]}"
    with admin.connect() as c:
        c.execute(text(f"CREATE DATABASE {name}"))
    url = make_url(base).set(database=name).render_as_string(hide_password=False)

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "backend" / "migrations"))
    old = os.environ.get("MAKOS_DATABASE_URL")
    os.environ["MAKOS_DATABASE_URL"] = url
    command.upgrade(cfg, "head")
    yield url
    if old is None:
        os.environ.pop("MAKOS_DATABASE_URL", None)
    else:
        os.environ["MAKOS_DATABASE_URL"] = old
    with admin.connect() as c:
        c.execute(text(f"DROP DATABASE {name} WITH (FORCE)"))
    admin.dispose()
