import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.contrib.auth.models import Group

from app.models import (
    JobType,
    Pro,
    ProBusiness,
    SupplyHouse,
)
from faker import Faker
from booking.models import ProductCatalog
from booking.tests.factories import (
    OrderFactory, SelectedProductFactory, CustomerLeadFactory, ProductCriteriaFactory)
from pro.serializers import CustomerAddressSerializer
from pro.tests.factories import (AppointmentFactory, CustomerAddressFactory, CustomerFactory, JobAddressFactory, ProBusinessAddressFactory, MaterialListFactory, JobFactory)
from random import randint


logger = logging.getLogger(__name__)


def insert_supplier_and_job_type():
    call_command('import_gsheet')


def insert_products_from_catalog():
    call_command('import_product_catalog')


def insert_test_users():
    us1 = Faker(["en_US"])
    pro, pro_created = Group.objects.get_or_create(name="pro")

    pro_user = (
        get_user_model().objects.filter(username="test-hb+pro@homebreeze.com").first()
    )
    if not pro_user:
        pro_user, _ = get_user_model().objects.get_or_create(
            username="test-hb+pro@homebreeze.com",
            first_name="Handy",
            last_name="McHanderson",
            email="test-hb+pro@homebreeze.com",
            phone='9176728148',  # https://smsreceivefree.com/info/19176728148/
        )
        if pro_user:
            pro_user.set_password(settings.TEST_PW)
            pro_user.save()
            pro_user.groups.add(pro)

    pro = Pro.objects.filter(user__last_name="McHanderson").first()

    if not pro:
        pro_business, _ = ProBusiness.objects.get_or_create(
            name="Pipes N'at",
            owner=pro_user,
            address=ProBusinessAddressFactory.create(),
        )

        pro, _ = Pro.objects.get_or_create(
            user=pro_user,
            business=pro_business,
        )


def insert_test_data():
    pro_business = ProBusiness.objects.get(name="Pipes N'at")
    for i in range(20):
        customer_lead = CustomerLeadFactory.create()
        ProductCriteriaFactory.create(customer_lead=customer_lead)

        product_catalog = ProductCatalog.objects.order_by('?').first()
        selected_product = SelectedProductFactory.create(
            customer_lead=customer_lead, product_catalog=product_catalog)
        customer_address = CustomerAddressFactory.create()
        appointment = AppointmentFactory.create()
        customer = CustomerFactory.create(address=customer_address, lead=customer_lead)
        job_address = JobAddressFactory.create(**(CustomerAddressSerializer(customer_address).data))

        job = JobFactory.create(
            customer=customer, address=job_address, appointment=appointment,
            type=None, scope=None, pro_business=None, is_pro_finished=False, job_created__no_invoice=True)
        order = OrderFactory.create(
            customer=customer, appointment=appointment, selected_product=selected_product)

        if(i > 5):
            job_type = JobType.objects.order_by('?').first()
            supply_house = SupplyHouse.objects.order_by('?').first()

            job.type = job_type
            job.scope = job_type.scope
            job.save()
            if(i > 10):
                MaterialListFactory.create(job=job, supply_house=supply_house)
                job.pro_business = pro_business
                job.save()
                if(i > 15):
                    job.is_pro_finished = True
                    job.save()
