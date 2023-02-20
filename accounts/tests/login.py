import re
import responses
from rest_framework import status
from rest_framework.test import APITransactionTestCase
from .factories import CustomUserFactory, ProUserFactory, GroupFactory
from accounts.models import CustomUser
import pyotp
from faker import Faker
import json
faker = Faker(locale="en_US")

class LoginTests(APITransactionTestCase):
    def send_sms(self):
        group = GroupFactory.create(name="pro")
        user = CustomUserFactory.create(phone="3854882735")
        user.groups.add(group)
        ProUserFactory.create(user=user)

        responses.post(
            re.compile("https://api.twilio.com/2010-04-01/Accounts/"),
            json={},
        )

        return self.client.post(f"/api/pro/auth/send-sms/{user.phone}/")

    @responses.activate
    def test_login_send_sms(self):
        response = self.send_sms()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_pro_login(self):
        self.send_sms()
        number = "+13854882735"
        user_with_phone = CustomUser.get_custom_user_with_number(number)
        time_otp = pyotp.TOTP(user_with_phone.sms_key, interval=900)
        code = time_otp.now()
        data = {
            "number": number,
            "code" : code
        }
        response = self.client.post(f"/api/pro/auth/login/", json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
