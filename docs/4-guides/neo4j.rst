.. _neo4j:

Neo4j
=====

When ``use_neo4j`` is ``y``, the generated project includes Neo4j_ (Community edition)
alongside PostgreSQL, with neomodel_ on the Django side.

.. _Neo4j: https://neo4j.com/docs/
.. _neomodel: https://neomodel.readthedocs.io/


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
* A ``graph`` Django app that points neomodel at Neo4j on startup, and an ``install_labels``
  management command that creates the constraints and indexes declared on your node classes.
* A ``neo4j_db`` pytest fixture that runs a test inside a transaction and rolls it back.
* ``backup``, ``backups``, ``restore`` and ``rmbackup`` maintenance scripts in the Neo4j image,
  mirroring the PostgreSQL ones.


Configuration
-------------

The ``.neo4j`` env files are read by both the ``neo4j`` container and Django:

``NEO4J_AUTH``
    ``neo4j/<password>``. The official image uses it to set the password when the database
    is first created; Django uses it to build its connection URL. Changing it later does not
    change the password of an existing database: run
    ``ALTER CURRENT USER SET PASSWORD FROM '<old>' TO '<new>'`` in Neo4j Browser first.
    Stick to letters and digits, because the password also goes inside a ``bolt://`` URL.

Any other ``NEO4J_*`` variable
    Becomes a Neo4j setting (``NEO4J_server_memory_heap_max__size`` is
    ``server.memory.heap.max_size``). Neo4j refuses to start on unknown settings, so don't put
    unrelated ``NEO4J_*`` variables in these files.

``NEO4J_PLUGINS``
    A JSON list. Add ``"graph-data-science"`` for GDS, for example.

To use a server outside the Compose stack, such as Neo4j Aura, set ``NEOMODEL_DATABASE_URL``
(for example ``neo4j+s://neo4j:<password>@<id>.databases.neo4j.io``) in the ``.django``
env file. The Django entrypoint then stops waiting for the bundled service, which you can remove.


Working with nodes
------------------

Define nodes in an app's ``models.py``, or import them there, so Django loads them::

    from neomodel import StringProperty
    from neomodel import StructuredNode
    from neomodel import UniqueIdProperty


    class Company(StructuredNode):
        uid = UniqueIdProperty()
        name = StringProperty(unique_index=True, required=True)

Then create the constraints and indexes, the way you would run migrations::

    $ docker compose -f docker-compose.local.yml run --rm django python manage.py install_labels

neomodel connects lazily, once per process, on the first query. Management commands that
don't touch the graph don't need Neo4j to be running.


Testing
-------

Neo4j Community has a single database, which tests share with local development. Use the
``neo4j_db`` fixture so the test runs in a transaction that is rolled back afterwards::

    def test_company_name(neo4j_db):
        Company(name="Acme").save()
        assert Company.nodes.get(name="Acme").name == "Acme"

Code that opens its own neomodel transaction (``with db.transaction:``) can't run inside the
fixture, since neomodel doesn't nest transactions; clean up after such tests instead.


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
