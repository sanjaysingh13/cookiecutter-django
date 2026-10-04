import atexit

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from {{ cookiecutter.project_slug }}.graph.driver import close_driver


class GraphConfig(AppConfig):
    name = "{{ cookiecutter.project_slug }}.graph"
    verbose_name = _("Graph")

    def ready(self):
        """
        Close this process's Neo4j driver when the process exits.
        """
        atexit.register(close_driver)
