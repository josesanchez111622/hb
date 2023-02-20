from typing import Tuple
from urllib.parse import urlencode
from httplib2 import Response
from rest_framework.test import APITransactionTestCase
from booking.models import CustomerLead, ProductCriteria
from booking.views import TANK_TYPEFORM_ID, TANKLESS_TYPEFORM_ID

# Sample API post data from Webflow, before Typeform:
# Endpoint will receive params from Webflow:
# {
#     "power_type": "gas|electric",
#     "bathroom_coverage": "1|2|3|4_or_more",
#     "tank_type": "tank|tankless",
# }
#
# and then forward to Typeform:
# {
#     "power_type": "gas|electric",
#     "bathroom_coverage": "1|2|3|4_or_more",
#     "url_token": "...",
# }


class CustomerUrlTokenTests(APITransactionTestCase):
    def get_response_data(self, tank_type, form_id) -> Tuple[Response, str]:
        url_params = {
            "power_type": "xxx",
            "bathroom_coverage": "xxx",
            "tank_type": "tank",
        }
        url_string = "/api/booking/webflow/"
        url_params["tank_type"] = tank_type

        request_url = f'{url_string}?{urlencode(url_params)}'
        response = self.client.get(request_url, follow=False)

        customer_lead = CustomerLead.objects.first()
        url_token = customer_lead.url_token
        redirect_params = {
            "power_type": "xxx",
            "bathroom_coverage": "xxx",
            "url_token": url_token
        }
        redirect_url = f'https://form.typeform.com/to/{form_id}?{urlencode(redirect_params)}'

        return response, redirect_url

    def test_webflow_redirect_tank(self):
        response, redirect_url = self.get_response_data(
            tank_type="tank", form_id=TANK_TYPEFORM_ID)
        self.assertRedirects(response, redirect_url,
                             fetch_redirect_response=False)

        product_criteria = ProductCriteria.objects.first()
        self.assertEqual(product_criteria.tank_type, "tank")
        customer_lead = CustomerLead.objects.first()
        self.assertEqual(product_criteria.customer_lead.id, customer_lead.id)

    def test_webflow_redirect_tankless(self):
        response, redirect_url = self.get_response_data(
            tank_type="tankless", form_id=TANKLESS_TYPEFORM_ID)
        self.assertRedirects(response, redirect_url,
                             fetch_redirect_response=False)

        product_criteria = ProductCriteria.objects.first()
        self.assertEqual(product_criteria.tank_type, "tankless")
        customer_lead = CustomerLead.objects.first()
        self.assertEqual(product_criteria.customer_lead.id, customer_lead.id)
