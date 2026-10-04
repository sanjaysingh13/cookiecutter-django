"""
The Neo4j driver, one per process.

The driver is created on first use, never at import time, so every Gunicorn
worker and Celery process opens its own connection pool, and commands that
don't touch the graph don't need Neo4j running.
"""

from __future__ import annotations

import threading
from functools import cache
from typing import TYPE_CHECKING
from typing import Any

from django.conf import settings
from neo4j import GraphDatabase

if TYPE_CHECKING:
    from typing import LiteralString

    from neo4j import Driver
    from neo4j import EagerResult
    from neo4j import Query
    from neo4j import Session

_lock = threading.Lock()


@cache
def _create_driver() -> Driver:
    return GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
    )


def get_driver() -> Driver:
    """Return this process's driver, creating it on first use."""
    with _lock:
        return _create_driver()


def get_session(**config: Any) -> Session:
    """Open a session on NEO4J_DATABASE. Use it in a ``with`` block."""
    return get_driver().session(database=settings.NEO4J_DATABASE, **config)


def execute_query(
    query: LiteralString | Query,
    parameters: dict[str, Any] | None = None,
    **kwargs: Any,
) -> EagerResult:
    """
    Run one query in its own transaction on NEO4J_DATABASE, retrying transient errors.

    Keyword arguments are query parameters, except driver options ending in an
    underscore, such as ``routing_=RoutingControl.READ``.
    """
    kwargs.setdefault("database_", settings.NEO4J_DATABASE)
    return get_driver().execute_query(query, parameters, **kwargs)


def close_driver() -> None:
    """Close this process's driver, if it created one."""
    with _lock:
        if _create_driver.cache_info().currsize:
            _create_driver().close()
            _create_driver.cache_clear()
