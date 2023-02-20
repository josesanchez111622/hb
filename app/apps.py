from django.apps import AppConfig
import analytics
from django.conf import settings


class AppConfig(AppConfig):
    name = 'app'

    def ready(self):
        analytics.write_key = settings.SEGMENT_WRITE_KEY
