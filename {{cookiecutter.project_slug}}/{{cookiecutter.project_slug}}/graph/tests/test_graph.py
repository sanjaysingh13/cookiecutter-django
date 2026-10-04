from neomodel import StringProperty
from neomodel import StructuredNode
from neomodel import db


class ConnectionProbe(StructuredNode):
    """Throwaway node type used to check the Neo4j wiring."""

    name = StringProperty(required=True)


def test_neo4j_is_reachable(neo4j_db):
    results, _ = neo4j_db.cypher_query("RETURN 1")
    assert results == [[1]]


def test_nodes_saved_inside_the_fixture_are_readable(neo4j_db):
    ConnectionProbe(name="Ada").save()
    assert ConnectionProbe.nodes.get(name="Ada").name == "Ada"


def test_rollback_discards_changes():
    db.begin()
    try:
        ConnectionProbe(name="Grace").save()
    finally:
        db.rollback()
    assert ConnectionProbe.nodes.get_or_none(name="Grace") is None
