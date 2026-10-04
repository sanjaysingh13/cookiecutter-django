.. _neo4j:

Neo4j
=====

When ``use_neo4j`` is ``y``, the generated project includes Neo4j_ (Community edition)
alongside PostgreSQL, with the official `Neo4j Python driver`_ on the Django side.

.. _Neo4j: https://neo4j.com/docs/
.. _Neo4j Python driver: https://neo4j.com/docs/python-manual/current/


What you get
------------

* A ``neo4j`` service in ``docker-compose.local.yml`` and ``docker-compose.production.yml``,
  built from ``compose/production/neo4j/Dockerfile`` on top of the official image.
  Locally, Neo4j Browser is published on http://localhost:7474 (Bolt on 7687); in production
  no ports are published and Django reaches it over the Compose network.
* APOC, enabled with ``NEO4J_PLUGINS=["apoc"]``. The image ships the APOC jar that matches
  its Neo4j version, so upgrading Neo4j never leaves you with a mismatched plugin.
* ``.envs/.local/.neo4j`` and ``.envs/.production/.neo4j``, holding ``NEO4J_AUTH`` (with a
  generated password), the plugin list, memory settings and APOC file import/export settings.
* A ``graph`` Django app whose ``driver.py`` keeps one driver per process, with
  ``get_driver()``, ``get_session()`` and ``execute_query()`` helpers.
* A ``neo4j_tx`` pytest fixture: a transaction that is rolled back after the test.
* ``backup``, ``backups``, ``restore`` and ``rmbackup`` maintenance scripts in the Neo4j image,
  mirroring the PostgreSQL ones.


Configuration
-------------

The ``.neo4j`` env files are read by both the ``neo4j`` container and Django:

``NEO4J_AUTH``
    ``neo4j/<password>``. The official image uses it to set the password when the database
    is first created; Django uses it to authenticate. Changing it later does not change the
    password of an existing database: run
    ``ALTER CURRENT USER SET PASSWORD FROM '<old>' TO '<new>'`` in Neo4j Browser first.
    The password can't contain a ``/``.

Any other ``NEO4J_*`` variable
    Becomes a Neo4j setting (``NEO4J_server_memory_heap_max__size`` is
    ``server.memory.heap.max_size``). Neo4j refuses to start on unknown settings, so don't put
    unrelated ``NEO4J_*`` variables in these files.

``NEO4J_PLUGINS``
    A JSON list. Add ``"graph-data-science"`` for GDS, for example.

Django also reads two variables of its own, prefixed ``DJANGO_`` so the Neo4j image doesn't
mistake them for settings:

``DJANGO_NEO4J_URI``
    Defaults to ``bolt://neo4j:7687``, the bundled service. To use another server, such as
    Neo4j Aura, set it in the ``.django`` env file (``neo4j+s://<id>.databases.neo4j.io``) along
    with that server's ``NEO4J_AUTH``. The Django entrypoint then stops waiting for the bundled
    service, which you can remove.

``DJANGO_NEO4J_DATABASE``
    Defaults to ``neo4j``, the only database in Community edition.


Working with the graph
----------------------

``<project_slug>/graph/driver.py`` creates the driver on first use in each process, so
Gunicorn workers and Celery processes each get their own connection pool, and commands that
don't touch the graph don't need Neo4j to be running. For a single query::

    from my_project.graph.driver import execute_query

    records, summary, keys = execute_query(
        "MERGE (c:Company {name: $name}) RETURN c",
        name="Acme",
    )

``execute_query`` runs on ``DJANGO_NEO4J_DATABASE`` and retries transient errors. For several
queries in one transaction, write a function that takes the transaction and run it through a
session::

    from my_project.graph.driver import get_session


    def rename_company(tx, old, new):
        tx.run("MATCH (c:Company {name: $old}) SET c.name = $new", old=old, new=new)


    with get_session() as session:
        session.execute_write(rename_company, "Acme", "Acme Corp")

Keep constraints and indexes as Cypher with ``IF NOT EXISTS``, for example
``CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE``,
so they can run on every deploy.

Prefer an object mapper? Add neomodel_ to your requirements and point it at the same
``NEO4J_URI`` and ``NEO4J_AUTH`` settings.

.. _neomodel: https://neomodel.readthedocs.io/


Testing
-------

Neo4j Community has a single database, which tests share with local development. The
``neo4j_tx`` fixture is a transaction that is rolled back after the test, so pass it to
functions written like ``rename_company`` above::

    def test_rename_company(neo4j_tx):
        neo4j_tx.run("CREATE (:Company {name: 'Acme'})")
        rename_company(neo4j_tx, "Acme", "Acme Corp")
        result = neo4j_tx.run("MATCH (c:Company {name: 'Acme Corp'}) RETURN count(c) AS n")
        assert result.single(strict=True)["n"] == 1

Code that runs its own queries through ``execute_query`` or a new session commits them, so
clean up after such tests yourself.


Backups
-------

Community edition can't dump a running database, so Neo4j is stopped while a backup runs.
Locally, ``just neo4j-backup`` and ``just neo4j-restore <file>`` do the stop, run and start
for you. Against production::

    $ docker compose -f docker-compose.production.yml stop neo4j
    $ docker compose -f docker-compose.production.yml run --rm neo4j backup
    $ docker compose -f docker-compose.production.yml start neo4j

Backups are stored in the Neo4j backups volume as ``backup_neo4j_<timestamp>.dump``.
``run --rm neo4j backups`` lists them, ``run --rm neo4j rmbackup <file>`` deletes one, and
``run --rm neo4j restore <file>`` replaces the database with one (also with Neo4j stopped).
If you run the backup while Neo4j is up, ``neo4j-admin`` refuses with "The database is in use",
and the script tells you to stop it first.

With AWS as the cloud provider, ``docker compose -f docker-compose.production.yml run --rm awscli upload``
uploads the Neo4j backups to ``s3://<bucket>/backups/neo4j/`` together with the PostgreSQL ones.
Download one back with ``run --rm awscli download neo4j/<file>``.


Upgrading Neo4j
---------------

Change the image tag in ``compose/production/neo4j/Dockerfile``, take a backup, then rebuild
and restart the ``neo4j`` service. Check Neo4j's upgrade guide first when moving from 5.26 to
a calendar release.
