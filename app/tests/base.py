from booking.tests.factories import CatalogWorksheetRowFactory
import responses
from django.contrib.auth import get_user_model
from django.test import TestCase

from django.core.management import call_command
from django.urls import reverse

from accounts.models import CustomUser


class AppTest(TestCase):
    username = ""
    password = ""

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

        call_command('testdata')

    def user(self) -> CustomUser:
        return get_user_model().objects.filter(username=self.username).first()

    def login(self) -> bool:
        result = self.client.login(username=self.username, password=self.password)
        self.assertTrue(result)

        return result

    def logout(self):
        # self.client.logout()
        pass

    def url(self, name, params={}):
        return reverse(name, kwargs=params)

    def post(self, name, params={}):
        return self.client.post(self.url(name, params))

    def get(self, name, params={}):
        return self.client.get(self.url(name, params))
