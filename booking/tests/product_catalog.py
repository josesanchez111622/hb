import responses
from django.core.management import call_command
from django.test import TestCase

from booking.tests.factories import CatalogWorksheetRowFactory


class ProductCatalogImportTest(TestCase):
    @responses.activate
    def test_import_product_catalog(self):
        responses.post("https://oauth2.googleapis.com/token", json={
            "access_token": "access_token",
        })
        responses.get("https://sheets.googleapis.com/v4/spreadsheets/1nfCT-xEXJYAc8wXecUIcqRhC4UM50J1AIK3_jLphZWg?includeGridData=false", json={
            "sheets": [{"properties": {"title": "Product Catalog"}}],
            "properties": {"title": "Product Catalog"},
        })

        responses.get("https://sheets.googleapis.com/v4/spreadsheets/1nfCT-xEXJYAc8wXecUIcqRhC4UM50J1AIK3_jLphZWg/values/%27Product%20Catalog%27", json={
            "values": [
                [
                    'Product Title',
                    'Description',
                    'Type',
                    'Home Type',
                    'Power Source',
                    'Bathrooms in Home',
                    'Current Location',
                    'Desired Location',
                    'Presence of Stairs',
                    'Brand',
                    'Popular Choice',
                    'Base Price',
                    'Unit Type',
                    'Home Coverage (People)',
                    'Water Flow (GPM)',
                    'Power Output (BTU)',
                    'Warranty (Years)',
                    'Total Rebates',
                    'SoCal Gas Rebate',
                    'Federal Tax Credit',
                ],
                list(CatalogWorksheetRowFactory.create().values()),
                list(CatalogWorksheetRowFactory.create().values()),
            ],
            "majorDimension": "ROWS",
            "range": "Product Catalog!A1:C2",
        })

        call_command('import_product_catalog')
        return super().setUp()
