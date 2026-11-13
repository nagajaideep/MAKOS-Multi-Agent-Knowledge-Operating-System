"""Shared SQLAlchemy base: core and every domain pack register their tables here."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
