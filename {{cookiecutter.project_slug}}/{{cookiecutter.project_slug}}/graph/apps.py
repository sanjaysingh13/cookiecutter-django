import atexit

from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from neomodel import db
from neomodel import get_config


class GraphConfig(AppConfig):
    name = "{{ cookiecutter.project_slug }}.graph"
    verbose_name = _("Graph")

    def ready(self):
        """
        Point neomodel at Neo4j.

        Nothing connects here: neomodel opens its driver on the first query in each
        process, so commands that never touch the graph don't need Neo4j running.
        """
        get_config().update(database_url=settings.NEOMODEL_DATABASE_URL)
        atexit.register(db.close_connection)
