from rest_framework import status
from rest_framework.test import APITransactionTestCase
from booking.tests.factories import (
    ProductCriteriaFactory,
    TypeformResponseDataFactory,
    CustomerLeadFactory)
from booking.models import TankType

# Sample API post data from Typeform:
# "form_response": {
#     "form_id": "",
#     "token": "",
#     "answers": [],
#     "definition": {},
#     "variables": [
#     {
#         "key": "coverage",
#         "type": "text",
#         "text": "2"
#     },
#     {
#         "key": "home",
#         "type": "text",
#         "text": "single_family"
#     },
#     {
#         "key": "power",
#         "type": "text",
#         "text": "gas"
#     },
#     {
#         "key": "relocation",
#         "type": "text",
#         "text": "current"
#     },
#     {
#         "key": "score",
#         "type": "number",
#         "number": 0
#     },
#     {
#         "key": "stairs",
#         "type": "text",
#         "text": "no"
#     },
#     {
#         "key": "tank_type",
#         "type": "text",
#         "text": "tankless"
#     },
#     {
#         "key": "customer_url_token",
#         "type": "text",
#         "text": "12345"
#     }
# ],
# }


class ProductCriteriaTests(APITransactionTestCase):
    def test_endpoint_with_customer(self):

        typeform_response_data = TypeformResponseDataFactory.create(
            form_response__form_id="A",
            form_response__token="B"
        )

        url_token = typeform_response_data.get(
            'form_response').get('hidden').get('url_token')

        customer_lead = CustomerLeadFactory.create(url_token=url_token)
        ProductCriteriaFactory.create(customer_lead=customer_lead)

        response = self.client.post(
            "/api/booking/typeform/", typeform_response_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('customer_lead'), customer_lead.id)
        self.assertEqual(response.data.get('tank_type'), TankType.Tankless)

    def test_error_response_with_customer(self):
        bad_typeform_response_data = TypeformResponseDataFactory.create(
            form_response__form_id="C",
            form_response__token="D"
        )
        del bad_typeform_response_data['form_response']['definition']

        response = self.client.post(
            "/api/booking/typeform/", bad_typeform_response_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
