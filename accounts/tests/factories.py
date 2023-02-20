import factory
from faker import Faker
from app.models import (
    ProBusiness,
    Pro,
)

from accounts.models import CustomUser
from django.contrib.auth.models import Group
from pro.tests.factories import ProBusinessFactory

faker = Faker(locale="en_US")

class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ['name']

    name: str = factory.LazyAttribute(lambda _: faker.pystr(max_chars=5))
class CustomUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser
        django_get_or_create = ['phone']

    username: str = factory.LazyAttribute(lambda _: faker.user_name())
    first_name: str = factory.LazyAttribute(lambda _: faker.first_name())
    last_name: str = factory.LazyAttribute(lambda _: faker.last_name())
    email: str = factory.LazyAttribute(lambda _: faker.email())
    password: str = factory.LazyAttribute(lambda _: faker.password())
    phone : str = factory.LazyAttribute(lambda _: faker.phone_number())

class ProUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pro
        django_get_or_create = ['user']

    business: ProBusiness = factory.SubFactory(ProBusinessFactory)
    user: CustomUser = factory.SubFactory(CustomUserFactory)