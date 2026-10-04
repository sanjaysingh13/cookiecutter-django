from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

{% if cookiecutter.use_neo4j == 'y' -%}
from {{ cookiecutter.project_slug }}.graph.driver import get_session
{% endif -%}
from {{ cookiecutter.project_slug }}.users.tests.factories import UserFactory

if TYPE_CHECKING:
{%- if cookiecutter.use_neo4j == 'y' %}
    from collections.abc import Iterator

    from neo4j import Transaction
{% endif %}
    from {{ cookiecutter.project_slug }}.users.models import User


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory.create()
{%- if cookiecutter.use_neo4j == 'y' %}


@pytest.fixture
def neo4j_tx() -> Iterator[Transaction]:
    """
    A Neo4j transaction that is rolled back after the test.

    Neo4j Community has a single database, shared with local development, so
    tests shouldn't commit. Write graph code as functions of a transaction, such
    as ``create_company(tx, name)``: the app runs them with
    ``session.execute_write(create_company, name)`` and tests pass this fixture.
    """
    with get_session() as session:
        tx = session.begin_transaction()
        yield tx
        if not tx.closed():
            tx.rollback()
{%- endif %}
