import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from booking.models import ProductCatalog
from booking.tests.factories import (CustomerLeadFactory, ProductCriteriaFactory)

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if ProductCatalog.objects.count() == 0:
            call_command('import_product_catalog')

        customer_lead = CustomerLeadFactory.create()
        ProductCriteriaFactory.create(customer_lead=customer_lead)
        base_url = os.getenv("REACT_APP_BASE_URL", "http://localhost:3000/")
        print(f"{base_url}site/booking/choose-product/?url_token={customer_lead.url_token}")
