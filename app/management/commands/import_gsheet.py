from __future__ import print_function
import os.path
from django.conf import settings
from django.core.management.base import BaseCommand
import gspread
from gspread import Client

from app.models import (JobType, SupplyHouse, SupplyHouseAddress)
from pro.helper.phone import get_formatted_phone

class Command(BaseCommand):
    def authorize(self) -> Client:
        credentialsPath = os.path.join(
            settings.BASE_DIR, settings.GS_CREDENTIALS_PATH)
        return gspread.service_account(filename=credentialsPath)

    def import_supply_house(self, account: Client):
        sheet = account.open_by_key(settings.GSHEET_ID).get_worksheet_by_id(0)
        records = sheet.get_all_records()

        results = []
        duplicated = []
        for record in records:

            supply_house_address, address_created = SupplyHouseAddress.objects.update_or_create(
                line1=record.get('Line 1'),
                line2=record.get('Line 2'),
                city=record.get('City'),
                state=record.get('State'),
                zip_code=record.get('Zip'),
                country="US"
            )

            supply_house, created = SupplyHouse.objects.update_or_create(
                brand=record.get('Supplier Brand'),
                name=record.get('Supplier'),
                phone=get_formatted_phone(record.get('Phone')),
                address=supply_house_address
            )
            results.append(supply_house)

        print(f'{len(results)} suppliers ({len(duplicated)} duplicates) imported!')

    def get_job_type(self, value: str):
        if("Water Heater Installation" in value):
            return "Tank Installation"
        return "Tankless Installation"

    def import_job_types(self, account: Client):
        sheet = account.open_by_key(settings.G_JOBTYPES_SHEET_ID).worksheet(
            'Untitled Database b90766ddaf164c0b8c41d9c14b8e0ab3')
        records = sheet.get_all_records()

        results = []
        duplicated = []
        for record in records:
            name = record.get('Job Type')
            parts = record.get('Parts List')
            scope = record.get('Task List')

            job_type, created = JobType.objects.update_or_create(
                name=name,
                type=self.get_job_type(name),
                scope=scope,
                defaults={
                    'name': name,
                    'type': self.get_job_type(name),
                    'scope': scope
                }
            )

            if not created:
                duplicated.append(job_type)
            results.append(job_type)
        print(f'{len(results)} job types ({len(duplicated)} duplicates) imported!')

    def handle(self, *args, **kwargs):
        account = self.authorize()
        if not account:
            print('Authorization Failed.')
            return
        print('Authorized.')

        self.import_job_types(account)
        self.import_supply_house(account)
