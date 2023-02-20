import responses

from rest_framework import status
from jsonschema import validate
from django.core.management import call_command

from rest_framework.test import APITestCase
from booking.models import ProductCatalog, ProductCriteria
from booking.serializers import ProductCriteriaSerializer
from booking.tests.factories import CatalogWorksheetRowFactory, CustomerLeadFactory, ProductCriteriaFactory


class SelectProductTests(APITestCase):

    @classmethod
    @responses.activate
    def setUpTestData(cls):
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
        cls.customer_lead = CustomerLeadFactory.create(url_token="12345")
        ProductCriteriaFactory.create(customer_lead=cls.customer_lead)

    def test_selected_product_list(self):
        product_catalog_schema = {
            "type": "array",
            "items": {
                "additionalProperties": False,
                "type": "object",
                "properties": {
                    "home_type": {"type": "string"},
                    "is_popular": {"type": "boolean"},
                    "warranty": {"type": "integer"},
                    "home_coverage": {"type": "string"},
                    "base_price": {"type": "integer"},
                    "stair_price": {"type": "integer"},
                    "total_rebates": {"type": "integer"},
                    "relocation": {"type": "string"},
                    "products": {
                        "type": "array",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "tank_type": {"type": "string"},
                            # "product_image": {"type": "string"},
                            "bathroom_coverage": {"type": "integer"},
                            "water_flow_gpm": {"type": "string"},
                        }
                    },
                },
            },
        }

        response = self.client.get(
            f"/api/booking/product/selected/{self.customer_lead.url_token}", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        validate(response.json()['product_catalog'], product_catalog_schema)

    def test_select_product(self):
        post_data = {
            "url_token": self.customer_lead.url_token,
            "product_catalog_id": ProductCatalog.objects.first().id,
        }

        response = self.client.post(
            f"/api/booking/select_product/", post_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIs(type(response.data), int)

        response = self.client.post(
            f"/api/booking/select_product/", post_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(type(response.data), int)

    def test_update_product_criteria(self):
        product_criteria = ProductCriteria.objects.first()
        post_data = ProductCriteriaSerializer(product_criteria).data

        response = self.client.post(
            f"/api/booking/update_product_criteria/", post_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(type(response.data), int)
