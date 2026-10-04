from typing import Final

from django.conf import settings

from {{ cookiecutter.project_slug }}.graph.driver import close_driver
from {{ cookiecutter.project_slug }}.graph.driver import execute_query
from {{ cookiecutter.project_slug }}.graph.driver import get_driver
from {{ cookiecutter.project_slug }}.graph.driver import get_session

COUNT_PROBES: Final = "MATCH (p:ConnectionProbe {name: $name}) RETURN count(p) AS n"


def test_execute_query_uses_the_configured_database():
    records, summary, _ = execute_query("RETURN $n AS n", n=1)
    assert records[0]["n"] == 1
    assert summary.database == settings.NEO4J_DATABASE


def test_neo4j_tx_sees_its_own_writes(neo4j_tx):
    neo4j_tx.run("CREATE (:ConnectionProbe {name: $name})", name="Ada")
    result = neo4j_tx.run(COUNT_PROBES, name="Ada")
    assert result.single(strict=True)["n"] == 1


def test_rolled_back_writes_are_discarded():
    with get_session() as session:
        tx = session.begin_transaction()
        tx.run("CREATE (:ConnectionProbe {name: $name})", name="Grace")
        tx.rollback()
        result = session.run(COUNT_PROBES, name="Grace")
        assert result.single(strict=True)["n"] == 0


def test_get_driver_returns_one_driver_per_process():
    assert get_driver() is get_driver()


def test_close_driver_lets_the_next_call_start_a_new_one():
    first = get_driver()
    close_driver()
    assert get_driver() is not first
