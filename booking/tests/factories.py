import random
import uuid
from faker import Faker
import factory
from booking.models import BathroomCoverage, HomeType, Order, OrderStatus, PowerType, Product, ProductCatalog, Relocation, SelectedProduct, TankType, TypeformResponse, ProductCriteria, CustomerLead
from pro.tests.factories import AppointmentFactory, CustomerFactory

faker = Faker(locale='en_US')

default_variables = [
    {
        "key": "coverage",
        "type": "text",
        "text": "1"
    },
    {
        "key": "home",
        "type": "text",
        "text": "single_family"
    },
    {
        "key": "power",
        "type": "text",
        "text": "gas"
    },
    {
        "key": "relocation",
        "type": "text",
        "text": "current"
    },
    {
        "key": "score",
        "type": "number",
        "number": 0
    },
    {
        "key": "stairs",
        "type": "text",
        "text": "no"
    },
    {
        "key": "tank_type",
        "type": "text",
        "text": "tankless"
    }]

default_hidden = {
        "url_token": "12345",
    }


class TypeformResponseDataFactory(factory.Factory):
    class Meta:
        model = dict

    form_response = factory.Dict({
        "form_id": "",
        "token": "",
        "answers": [],
        "definition": {},
        "variables": default_variables,
        "hidden": default_hidden,
    })


class TypeformResponseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TypeformResponse

    form_id = factory.LazyAttribute(lambda _: faker.uuid4())
    token = factory.LazyAttribute(lambda _: faker.uuid4())
    definition = {}
    variables = default_variables
    hidden = default_hidden


class ProductCriteriaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductCriteria

    typeform_response = factory.SubFactory(TypeformResponseFactory)


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    unit_type = factory.LazyAttribute(lambda _: faker.text())
    title = factory.LazyAttribute(lambda _: faker.text())
    brand = factory.LazyAttribute(lambda _: faker.text())
    description = factory.LazyAttribute(lambda _: faker.text())
    tank_type = factory.LazyAttribute(
        lambda _: random.choice(TankType.choices))
    product_image = factory.LazyAttribute(lambda _: faker.image_url())
    power_type = factory.LazyAttribute(
        lambda _: random.choice(PowerType.choices))
    bathroom_coverages = factory.LazyAttribute(lambda _: list(map(lambda x: x[0], random.sample(
        BathroomCoverage.choices, random.randint(1, len(BathroomCoverage.choices))))))
    water_flow_gpm = factory.LazyAttribute(lambda _: faker.text())
    power_output_btu = factory.LazyAttribute(lambda _: faker.text())
    home_coverage = factory.LazyAttribute(lambda _: faker.text())


class ProductCatalogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductCatalog

    home_types = factory.LazyAttribute(
        lambda _: random.choice(HomeType.choices))
    current_location = factory.LazyAttribute(
        lambda _: random.choice(Relocation.choices))
    desired_location = factory.LazyAttribute(
        lambda _: random.choice(Relocation.choices))
    is_popular = factory.LazyAttribute(lambda _: random.choice([True, False]))
    base_price = factory.LazyAttribute(lambda _: random.randint(1000, 6000))
    stair_price = factory.LazyAttribute(lambda _: random.choice([0, 100]))
    warranty = factory.LazyAttribute(lambda _: random.choice([6, 10, 12, 24]))
    total_rebates = factory.LazyAttribute(lambda _: random.randint(0, 1000))
    socal_gas_rebates = factory.LazyAttribute(
        lambda _: random.randint(0, 1000))
    federal_tax_credit = factory.LazyAttribute(
        lambda _: random.randint(0, 1000))
    product = factory.SubFactory(ProductFactory)


class CustomerLeadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomerLead

    url_token = factory.LazyAttribute(lambda _: faker.uuid4())


class SelectedProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SelectedProduct

    customer_lead = factory.SubFactory(CustomerLeadFactory)
    product_catalog = factory.SubFactory(ProductCatalogFactory)


def generate_calendly_scheduled_payload() -> dict:
    # https://github.com/tcampb/react-calendly

    event_uuid = str(uuid.uuid4())
    event_uri = f"https://api.calendly.com/scheduled_events/{event_uuid}"
    invitee_uuid = str(uuid.uuid4())
    invitee_uri = f"{event_uri}/invitees/{invitee_uuid}"

    return {"event": "calendly.event_scheduled",
            "payload": {"event": {"uri": event_uri},
                        "invitee": {"uri": invitee_uri}}}


class CalendlyEventResourceFactory(factory.DictFactory):
    # https://developer.calendly.com/api-docs/e2f95ebd44914-get-event

    uri = factory.LazyAttribute(lambda _: faker.uri())
    name = factory.LazyAttribute(lambda _: faker.text())
    status = factory.LazyAttribute(lambda _: random.choice([
        "active",
        "canceled",
    ]))
    booking_method = factory.LazyAttribute(lambda _: random.choice([
        "instant",
        "scheduled",
    ]))
    start_time = factory.LazyAttribute(lambda _: faker.iso8601())
    end_time = factory.LazyAttribute(lambda _: faker.iso8601())
    event_type = factory.LazyAttribute(lambda _: faker.uri())
    location = factory.Dict({
        "type": "physical",
        "location": factory.LazyAttribute(lambda _: faker.postcode())
    })
    invitees_counter = factory.Dict({
        "total": factory.LazyAttribute(lambda _: random.randint(0, 10)),
        "active": factory.LazyAttribute(lambda _: random.randint(0, 10)),
        "limit": factory.LazyAttribute(lambda _: random.randint(0, 20))
    })
    created_at = factory.LazyAttribute(lambda _: faker.iso8601())
    updated_at = factory.LazyAttribute(lambda _: faker.iso8601())
    event_memberships = factory.List([
        factory.Dict({
            "user": factory.LazyAttribute(lambda _: faker.uri())
        })
    ])
    event_guests = factory.List([
        factory.Dict({
            "email": factory.LazyAttribute(lambda _: faker.email()),
            "created_at": factory.LazyAttribute(lambda _: faker.iso8601()),
            "updated_at": factory.LazyAttribute(lambda _: faker.iso8601())
        })
    ])


class CalendlyInviteeResourceFactory(factory.DictFactory):
    # https://developer.calendly.com/api-docs/8305c0ccfac70-get-event-invitee

    cancel_url = factory.LazyAttribute(lambda _: faker.uri())
    created_at = factory.LazyAttribute(lambda _: faker.iso8601())
    email = factory.LazyAttribute(lambda _: faker.email())
    rescheduled = factory.LazyAttribute(lambda _: random.choice([
        True,
        False,
    ]))
    reschedule_url = factory.LazyAttribute(lambda _: faker.uri())
    event = factory.LazyAttribute(lambda _: faker.uri())
    name = factory.LazyAttribute(lambda _: faker.text())
    first_name = factory.LazyAttribute(lambda _: faker.first_name())
    last_name = factory.LazyAttribute(lambda _: faker.last_name())
    new_invitee = factory.LazyAttribute(lambda _: faker.uri())
    old_invitee = factory.LazyAttribute(lambda _: faker.uri())
    status = factory.LazyAttribute(lambda _: random.choice([
        "active",
        "canceled",
    ]))
    text_reminder_number = factory.LazyAttribute(
        lambda _: random.randint(0, 10))
    timezone = factory.LazyAttribute(lambda _: faker.timezone())
    tracking = factory.Dict({
        "utm_campaign": factory.LazyAttribute(lambda _: faker.uri()),
        "utm_source": factory.LazyAttribute(lambda _: faker.uri()),
        "utm_medium": factory.LazyAttribute(lambda _: faker.uri()),
        "utm_content": factory.LazyAttribute(lambda _: faker.uri()),
        "utm_term": factory.LazyAttribute(lambda _: faker.uri()),
        "salesforce_uuid": factory.LazyAttribute(lambda _: faker.uri())
    })
    updated_at = factory.LazyAttribute(lambda _: faker.iso8601())
    uri = factory.LazyAttribute(lambda _: faker.uri())
    questions_and_answers = factory.List([
        factory.Dict({
            "answer": factory.LazyAttribute(lambda _: faker.text()),
            "position": factory.LazyAttribute(lambda _: random.randint(0, 10)),
            "question": factory.LazyAttribute(lambda _: faker.text())
        })
    ])
    canceled = factory.LazyAttribute(lambda _: random.choice([
        True,
        False,
    ]))
    payment = factory.Dict({
        "external_id": factory.LazyAttribute(lambda _: faker.uri()),
        "provider": factory.LazyAttribute(lambda _: random.choice([
            "stripe",
            "paypal"
        ])),
        "amount": factory.LazyAttribute(lambda _: random.randint(0, 100)),
        "currency": factory.LazyAttribute(lambda _: faker.currency_code()),
        "terms": factory.LazyAttribute(lambda _: faker.text()),
        "successful": factory.LazyAttribute(lambda _: random.choice([
            True,
            False,
        ]))
    })
    no_show = factory.LazyAttribute(lambda _: random.choice([
        True,
        False,
    ]))
    reconfirmation = factory.Dict({
        "created_at": factory.LazyAttribute(lambda _: faker.iso8601()),
        "confirmed_at": factory.LazyAttribute(lambda _: faker.iso8601())
    })


class SubmitBookingFormFactory(factory.DictFactory):
    customer = factory.Dict({
        "id": factory.LazyAttribute(lambda _: random.randint(0, 10)),
        "first_name": factory.LazyAttribute(lambda _: faker.first_name()),
        "last_name": factory.LazyAttribute(lambda _: faker.last_name()),
        "email": factory.LazyAttribute(lambda _: faker.email()),
        "phone_number": factory.LazyAttribute(lambda _: faker.phone_number()),
        "address": factory.LazyAttribute(lambda _: faker.address()),
        "apt_number": factory.LazyAttribute(lambda _: faker.text()),
        "city": factory.LazyAttribute(lambda _: faker.city()),
        "zip_code": factory.LazyAttribute(lambda _: faker.postcode()),
        "gate_code": factory.LazyAttribute(lambda _: faker.text()),
    })
    appointment = factory.Dict({
        "date": factory.LazyAttribute(lambda _: faker.iso8601()),
    })
    selected_product = factory.Dict({
        "id": "",
    })

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    customer = factory.SubFactory(CustomerFactory)
    selected_product = factory.SubFactory(SelectedProductFactory)
    appointment = factory.SubFactory(AppointmentFactory)
    order_status = OrderStatus.Ordered

class CatalogWorksheetRowFactory(factory.DictFactory):
    product_title = factory.LazyAttribute(lambda _: faker.text())
    description = factory.LazyAttribute(lambda _: faker.text())
    type = factory.LazyAttribute(lambda _: random.choice([
        "Tankless Water Heater",
        "Tank Water Heater",
    ]))
    home_type = factory.LazyAttribute(lambda _: random.choice([
        "Single Family",
        "Townhome",
        "Condo",
        "Manufactured",
        "Manufactured, Single Family, Townhome, Condo",
        "Single Family, Townhome, Condo",
    ]))
    power_source = factory.LazyAttribute(
        lambda _: random.choice(["Gas", "Electric", "Propane"]))
    bathrooms_in_home = factory.LazyAttribute(lambda _: random.choice([
        "1, 2",
        "2, 3",
        "3",
        "3, 4 or more",
        "4 or more",
    ]))
    current_location = factory.LazyAttribute(lambda _: random.choice([
        "null",
        "Basement",
        "Current Location",
        "Garage",
        "Indoor Closet",
        "Outside over 10 feet from gas line",
        "Outside within 10 feet of gas line",
        "Tankless Water Heater",
    ]))
    desired_location = factory.LazyAttribute(lambda _: random.choice([
        "Basement",
        "Garage",
        "Indoor Closet",
        "null",
        "Outside over 10 feet from gas line",
        "Outside within 10 feet of gas line",
    ]))
    stair_price = factory.LazyAttribute(lambda _: random.choice([
        "$0",
        "$100",
    ]))
    brand = factory.LazyAttribute(lambda _: random.choice([
        "A.O. Smith",
        "Bradford White",
        "Navien",
        "Noritz",
        "Rheem",
        "Rinnai",
    ]))
    popular_choice = factory.LazyAttribute(
        lambda _: random.choice(["Yes", "No"]))
    base_price = factory.LazyAttribute(
        lambda _: f"${random.randint(1500, 5000):,}")
    unit_type = factory.LazyAttribute(lambda _: random.choice([
        "30 Gallon",
        "40 Gallon",
        "50 Gallon",
        "75 Gallon",
        "80 Gallon",
        "EZ111OD",
        "EZ98OD",
        "EZTR40",
        "EZTR50",
        "EZTR75",
        "NPE-150S",
        "NPE-180S",
        "NPE-210S",
        "NR662-OD",
        "RU130en",
        "RU130in",
        "RU160en",
        "RU160in",
        "RU180en",
        "RU180in",
    ]))
    home_coverage = factory.LazyAttribute(lambda _: random.choice([
        "1 - 3",
        "2 - 4",
        "3 - 5",
        "5 - 8",
    ]))
    water_flow = factory.LazyAttribute(lambda _: random.choice([
        faker.pyfloat(min_value=6, max_value=12, right_digits=1),
        "null",
    ]))
    power_output = factory.LazyAttribute(lambda _: random.choice([
        f"{faker.pyint(120, 200)}K",
        "null",
    ]))
    warranty = factory.LazyAttribute(
        lambda _: faker.pyint(min_value=6, max_value=15))
    total_rebates = factory.LazyAttribute(lambda _: random.choice([
        "$1,000",
        "$800",
        "null",
    ]))
    socal_gas_rebate = factory.LazyAttribute(lambda _: random.choice([
        "$1,000",
        "$800",
        "null",
    ]))
    federal_tax_credit = factory.LazyAttribute(lambda _: random.choice([
        "$0",
        "null",
    ]))
