from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
{%- if cookiecutter.use_neo4j == 'y' %}
from neomodel import db as neomodel_db
{%- endif %}

from {{ cookiecutter.project_slug }}.users.tests.factories import UserFactory

if TYPE_CHECKING:
{%- if cookiecutter.use_neo4j == 'y' %}
    from collections.abc import Iterator

    from neomodel.sync_.database import Database
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
def neo4j_db() -> Iterator[Database]:
    """
    Run the test inside a Neo4j transaction that is rolled back afterwards.

    Neo4j Community has a single database, shared with local development,
    so rolling back keeps it clean. Code that starts its own neomodel
    transaction can't run inside this fixture.
    """
    neomodel_db.begin()
    yield neomodel_db
    neomodel_db.rollback()
{%- endif %}
