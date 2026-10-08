"""
SQLAlchemy declarative base.
Imports all models here so Alembic detects them during autogenerate and migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
