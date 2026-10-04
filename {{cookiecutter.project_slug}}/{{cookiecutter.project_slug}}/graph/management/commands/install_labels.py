from typing import TYPE_CHECKING
from typing import cast

from django.core.management.base import BaseCommand
from neomodel import db

if TYPE_CHECKING:
    from typing import TextIO


class Command(BaseCommand):
    help = (
        "Create the Neo4j constraints and indexes declared on your node classes. "
        "Define nodes in an app's models.py (or import them there) so they are found."
    )

    def handle(self, *args, **options):
        # Django's OutputWrapper writes like a TextIO but isn't typed as one.
        db.install_all_labels(stdout=cast("TextIO", self.stdout))
