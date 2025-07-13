"""Base model for SQLAlchemy ORM."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from typing import Any

# Define naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

# Base model class for all database models using modern SQLAlchemy 2.0 syntax
class Base(DeclarativeBase):
    metadata = metadata 