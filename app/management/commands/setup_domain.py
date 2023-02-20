from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **options):
        site: Site = Site.objects.get(id=1)
        site.domain = settings.DEFAULT_FROM_DOMAIN.lower()
        site.name = settings.DEFAULT_FROM_DOMAIN
        site.save()
