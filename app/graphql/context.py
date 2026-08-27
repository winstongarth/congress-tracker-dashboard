from __future__ import annotations

from typing import TypedDict

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.graphql.loaders import Loaders, make_loaders


class GraphQLContext(TypedDict):
    db: Session
    loaders: Loaders


def get_graphql_context(db: Session = Depends(get_db)) -> GraphQLContext:
    # Reuses the same get_db dependency as every REST route, so tests that
    # override get_db (see tests/conftest.py) transparently cover GraphQL too,
    # and session lifecycle (close on request end) stays in one place.
    return {"db": db, "loaders": make_loaders(db)}
