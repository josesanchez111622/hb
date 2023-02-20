from django.core.management.base import BaseCommand

from app.test_data import insert_test_users, insert_test_data, insert_products_from_catalog, insert_supplier_and_job_type

class Command(BaseCommand):
    def handle(self, *args, **options):
        insert_products_from_catalog()
        insert_supplier_and_job_type()
        insert_test_users()
        insert_test_data()
