import gspread
import logging
import os

from gspread import Client
from django.conf import settings
from django.core.management.base import BaseCommand
from booking.models import (ProductCatalog, Product)
from app.helper import parseInt, isNum

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def authorize(self) -> Client:
        credentialsPath = os.path.join(
            settings.BASE_DIR, settings.GS_CREDENTIALS_PATH)
        return gspread.service_account(filename=credentialsPath)

    def handleTankType(self, value: str):
        if value == "Tank Water Heater":
            return "tank"
        if value == "Tankless Water Heater":
            return "tankless"

    def getHomeTypes(self, value: str):
        if(value == "Single Family"):
            return "single_family"
        elif(value == "Townhome"):
            return "townhome"
        elif(value == "Condo"):
            return "condo"
        elif(value == "Manufactured"):
            return "manufactured"

    def handleHomeType(self, value: str):
        if not value:
            return []

        value = value.strip()

        values = value.split(",")
        values = list(map(lambda x: self.getHomeTypes(x.strip()), values))
        return values

    def handleBathrooms(self, value: str):
        if not value:
            return []

        if isNum(value):
            return [value]

        value = value.strip()

        values = value.split(',')
        values = list(map(lambda x: x.strip().replace("'", ""), values))
        intValues = []
        for x in values:
            integer = parseInt(x)
            if integer > 0:
                intValues.append(integer)
            elif x == '4 or more':
                intValues.append(4)

        if len(intValues) >= 2:
            results = [intValues[i] for i in range(
                len(intValues)) if i == 0 or i == len(intValues)-1]
            return results

        return intValues

    def handlePowerType(self, value: str):
        if value == "Gas":
            return "gas"
        elif value == "Electric":
            return "electric"
        elif value == "Propane":
            return "propane"

    def handlePrice(self, value: str):
        if not value:
            return 0

        value = value.strip()
        if value == "null":
            return 0

        # Check $
        if value.count("$") != 1 or value[0] != "$":
            return 0

        try:
            return parseInt(value.replace("$", "").replace(",", ""))
        except:
            return 0

    def handleLocation(self, value: str):
        if value == "None" or not value:
            return "current"
        if value == "Indoor Closet":
            return "indoor_closet"
        if value == "Outside within 10 feet of gas line":
            return "outdoor_within_10_feet"
        if value == "Outside over 10 feet from gas line":
            return "outdoor_over_10_feet"
        if value == "Garage":
            return "garage"
        if value == "Basement":
            return "basement"
        return value

    def handleProductImage(self, value: str):
        return settings.GCS_PRODUCT_IMAGE + value + '.jpg'

    def map_record_to_product_data(self, record: dict):
        product_data = {
            'unit_type': record.get('Unit Type'),
            'title': record.get('Product Title'),
            'brand': record.get('Brand'),
            'description': record.get('Description'),
            'product_image': self.handleProductImage(record.get('Brand')),
            'tank_type': self.handleTankType(record.get('Type')),
            'power_type': self.handlePowerType(record.get('Power Source')),
            'bathroom_coverages': self.handleBathrooms(record.get('Bathrooms in Home')),
            'home_coverage': record.get('Home Coverage (People)'),
            'water_flow_gpm': record.get('Water Flow (GPM)'),
            'power_output_btu': record.get('Power Input (GPM)'),
        }

        product_catalog_data = {
            'total_rebates': self.handlePrice(record.get('Total Rebates')),
            'socal_gas_rebates': self.handlePrice(record.get('SoCal Gas Rebate')),
            'federal_tax_credit': self.handlePrice(record.get('Federal Tax Credit')),
            'warranty': record.get('Warranty (Years)'),
            'home_types': self.handleHomeType(record.get('Home Type')),
            'current_location': self.handleLocation(record.get('Current Location')),
            'desired_location': self.handleLocation(record.get('Desired Location')),
            'is_popular': record.get('Popular Choice') == 'Yes',
            'base_price': self.handlePrice(record.get('Base Price')),
            'stair_price': self.handlePrice(record.get('Presence of Stairs')),
        }

        return product_data, product_catalog_data

    def import_sheet(self, account: Client):
        sheet = account.open_by_key(
            settings.G_PRODUCT_CATALOG_SHEET_ID).worksheet("Product Catalog")
        records = sheet.get_all_records()

        results = []
        duplicated = []
        for record in records:
            product_data, product_catalog_data = self.map_record_to_product_data(
                record)

            try:
                product = Product.objects.get(title=product_data['title'])
            except Product.DoesNotExist:
                product, created = Product.objects.update_or_create(
                    **product_data,
                    defaults=product_data
                )

            product_catalog, created = ProductCatalog.objects.update_or_create(
                **product_catalog_data,
                product=product,
                defaults=product_catalog_data
            )

            if created:
                results.append(product_catalog)
            else:
                duplicated.append(product_catalog)

        logger.info(
            f'{len(results)}s product catalogs ({len(duplicated)}s duplicated) imported!')

    def handle(self, *args, **kwargs):
        account = self.authorize()
        if not account:
            logger.debug('Authorization Failed.')
            return

        logger.debug('Authorized.')

        self.import_sheet(account)
