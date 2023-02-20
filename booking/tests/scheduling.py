import responses
import re

from django.db.models import signals
from rest_framework.test import APITransactionTestCase
from rest_framework import status
from booking.models import CalendlyEvent, CalendlyInvitee
from app.models import Customer

from booking.tests.factories import (
    CalendlyEventResourceFactory,
    CalendlyInviteeResourceFactory,
    CustomerLeadFactory,
    generate_calendly_scheduled_payload)

from jsonschema import validate


class CalendlyDataTests(APITransactionTestCase):

    @responses.activate
    def setUp(self):
        signals.post_save.disconnect(
            sender=Customer, dispatch_uid="emit_identify_to_segment")

        self.customer_lead = CustomerLeadFactory.create(url_token="12345")
        self.event = {}
        self.invitee = {}

        calendly_data = generate_calendly_scheduled_payload()

        post_data = {
            "url_token": self.customer_lead.url_token,
            "calendly_data": calendly_data,
        }

        calendly_event_uri = calendly_data.get(
            'payload').get('event').get('uri')
        calendly_invitee_uri = calendly_data.get(
            'payload').get('invitee').get('uri')

        responses.get(calendly_event_uri, json={
            "resource": CalendlyEventResourceFactory.create(uri=calendly_event_uri)
        })

        responses.get(calendly_invitee_uri, json={
            "resource": CalendlyInviteeResourceFactory.create(uri=calendly_invitee_uri)
        })

        self.response = self.client.post(
            "/api/booking/calendly/", post_data, format="json")
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)

        self.event = CalendlyEvent.objects.first()
        self.invitee = CalendlyInvitee.objects.first()
        self.customer = Customer.objects.first()

    def test_fetch_calendly_data(self):
        self.assertEqual(self.event.id, self.invitee.id, self.response.data)
        self.assertGreater(len(self.invitee.uuid), 0)

    def test_get_customer_from_calendly_invitee(self):
        event_schema = {
            "additionalProperties": False,
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "uri": {"type": "string"},
                "name": {"type": "string"},
                "start_time": {"type": "string", "format": "date-time"},
                "location": {
                    "additionalProperties": False,
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "location": {"type": "string"},
                    }
                },
            },
        }

        calendly_invitee = {
            "additionalProperties": False,
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "uri": {"type": "string"},
                "uuid": {"type": "string"},
                "reschedule_url": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "email": {"type": "string"},
                "event": event_schema,
            },
        }

        customer_lead_schema = {
            "additionalProperties": False,
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "url_token": {"type": "string"},
                "product_criteria": {"type": ["string", "null"]},
                "selected_product": {"type": ["string", "null"]},
                "calendly_invitee": calendly_invitee,
            },
        }

        response = self.client.get(
            f"/api/booking/calendly_invitee/{self.invitee.uuid}", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('id'), self.customer.id)

        customer_lead_json = response.json()['lead']
        invitee_json = response.json()['lead']['calendly_invitee']
        event_json = response.json()['lead']['calendly_invitee']['event']

        validate(event_json, event_schema)
        validate(invitee_json, calendly_invitee)
        validate(customer_lead_json, customer_lead_schema)

    @responses.activate
    def test_handle_reschedule_calendly_data(self):
        post_data = {
            "url_token": self.customer_lead.url_token,
        }
        responses.post(
            re.compile("https://api.calendly.com/scheduled_events/"),
            json={},
        )
        response = self.client.post(
            "/api/booking/calendly/reschedule/", post_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(self.customer_lead.calendly_invitee)
        self.assertEqual(CalendlyEvent.objects.count(), 0)
        self.assertEqual(CalendlyInvitee.objects.count(), 0)
        self.assertEqual(Customer.objects.count(), 0)
