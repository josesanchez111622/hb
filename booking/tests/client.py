import responses
from rest_framework.test import APITransactionTestCase
from booking.client import CalendlyClient
from booking.tests.factories import CalendlyEventResourceFactory, generate_calendly_scheduled_payload
from booking.views import TANK_TYPEFORM_ID, TANKLESS_TYPEFORM_ID


class CalendlyClientTests(APITransactionTestCase):

    @responses.activate
    def test_get(self):
        calendly_data = generate_calendly_scheduled_payload()
        calendly_event_uri = calendly_data.get('payload').get('event').get('uri')

        responses.get(calendly_event_uri, json={
            "resource": CalendlyEventResourceFactory.create(uri=calendly_event_uri)
        })

        calendly_client = CalendlyClient()
        response_data = calendly_client.get(url=calendly_event_uri)

        self.assertEqual(response_data.get('resource').get('uri'), calendly_event_uri)
