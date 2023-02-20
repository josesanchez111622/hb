from rest_framework.test import APITransactionTestCase
from .factories import CustomUserFactory
import phonenumbers
from faker import Faker
faker = Faker(locale="en_US")

class LoginTests(APITransactionTestCase):
    def test_invalid_phone(self):
        with self.assertRaises(phonenumbers.phonenumberutil.NumberParseException):
            CustomUserFactory.create(phone="asdf")

    def test_valid_phone(self):
        phone = faker.phone_number()
        CustomUserFactory.create(phone=phone)
        self.assertTrue(True)