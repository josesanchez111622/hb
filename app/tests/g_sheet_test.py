from django.core.management import call_command

from .base import AppTest
from app.models import Supplier


class GSheetImportTest(AppTest):
    def test_google_sheet_import(self):
        old_count = Supplier.objects.count()

        call_command('import_gsheet')

        new_count = Supplier.objects.count()

        self.assertGreater(new_count, old_count)
