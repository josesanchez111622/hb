from rest_framework import status
from rest_framework.test import APITransactionTestCase
from app.models import Appointment, Customer, Job, Address
from booking.models import Order
from booking.serializers import SelectedProductSerializer
from booking.tests.factories import SelectedProductFactory, SubmitBookingFormFactory
from django.db.models import signals


class CustomerOrderTests(APITransactionTestCase):

    def test_submit_customer_order(self):
        signals.post_save.disconnect(
            sender=Customer, dispatch_uid="emit_identify_to_segment")
        signals.post_save.disconnect(
            sender=Order, dispatch_uid="post_order_to_slack")

        selected_product = SelectedProductFactory.create()
        post_data = SubmitBookingFormFactory.create(
            selected_product=SelectedProductSerializer(selected_product).data
        )

        response = self.client.post(
            "/api/booking/customer_order/", post_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        address = Address.objects.first()
        customer = Customer.objects.first()
        self.assertEqual(address.id, customer.address.id)

        job = Job.objects.first()
        appointment = Appointment.objects.first()
        self.assertEqual(job.appointment.id, appointment.id)
        self.assertEqual(job.customer.id, customer.id)

        last_job_note = job.job_notes.last()
        self.assertEqual(last_job_note.note,
                         f"GATE CODE: {customer.address.gate_code}")

        order = Order.objects.first()
        self.assertEqual(order.customer.id, customer.id)
        self.assertEqual(order.appointment.id, appointment.id)
