from typing import List
from urllib.parse import urlencode, urlparse
from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from app.models import Customer, Job, JobNote
from booking.serializers import CalendlyEventSerializer, CalendlyInviteeSerializer, CustomerLeadSerializer, ProductCatalogSerializer, TypeformSerializer, ProductCriteriaSerializer
from booking.models import CalendlyEvent, CalendlyInvitee, Order, ProductCatalog, ProductCriteria, CustomerLead, SelectedProduct
from booking.client import CalendlyClient
from pro.serializers import AppointmentSerializer, CustomerAddressSerializer, CustomerSerializer, AddressSerializer, JobAddressSerializer
from config.settings import TANK_TYPEFORM_ID, TANKLESS_TYPEFORM_ID


@api_view(['GET'])
def webflow_to_typeform_redirect(request: HttpRequest) -> HttpResponseRedirect:
    """ Sample API post data from Webflow, before Typeform:
        Endpoint will receive params from Webflow
        and then forward to Typeform

    Args:
        request (HttpRequest): GET request from Webflow link

    Returns:
        redirect (HttpResponseRedirect): redirection to external url with params
    """
    if request.method == 'GET':
        tank_type = request.GET.get('tank_type')
        form_id = TANK_TYPEFORM_ID if tank_type == 'tank' else TANKLESS_TYPEFORM_ID
        redirect_base_url = f'https://form.typeform.com/to/{form_id}'

        customer_lead = CustomerLead.objects.create()
        ProductCriteria.objects.create(
            customer_lead=customer_lead, tank_type=tank_type)
        url_params = {
            'power_type': request.GET.get('power_type'),
            'bathroom_coverage': request.GET.get('bathroom_coverage'),
            'url_token': customer_lead.url_token,
        }
        redirect_url = f'{redirect_base_url}?{urlencode(url_params)}'
        return redirect(redirect_url)


@api_view(['POST'])
def typeform_webhook(request: HttpRequest):
    """ Serialize and store customer's Typeform Response.
        First validate form response data, then store TypeformResponse.
        Lastly validate ProductCriteria data, and store ProductCriteria.

    Args:
        request (HttpRequest): POST request from Typeform webhook

    Returns:
        redirect: redirection to external url with params
    """
    if request.method == 'POST':
        serializer = TypeformSerializer(data=request.data['form_response'])

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        typeform_response = serializer.save()

        product_criteria_data = serializer.map_variables(
            serializer.validated_data.get('variables'))

        customer_lead_id = serializer.map_hidden(
            serializer.validated_data.get('hidden'))
        product_criteria_data['customer_lead'] = customer_lead_id
        product_criteria = ProductCriteria.objects.get(
            customer_lead=customer_lead_id)

        product_criteria_data['typeform_response'] = typeform_response.id
        product_criteria_serializer = ProductCriteriaSerializer(
            instance=product_criteria,
            data=product_criteria_data)

        if not product_criteria_serializer.is_valid():
            return Response(product_criteria_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_criteria_serializer.save()

        return Response(product_criteria_serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def selected_product_list(request: HttpRequest, url_token: str) -> List[ProductCatalog]:
    """ Provides a list of products that have been filtered for the customer.
        Used on Product Selection page.

    Args:
        request (HttpRequest): from django http
        url_token (str): string that uniquely identifies the CustomerLead

    Returns:
        List[ProductCatalog]: List of ProductCatalog objects that match the customer's ProductCriteria
    """
    customer_lead = CustomerLead.objects.get(url_token=url_token)
    if customer_lead == None:
        return Response("URL Token Is Invalid.", status=status.HTTP_400_BAD_REQUEST)

    product_criteria = ProductCriteria.get_criteria_with_customer_lead(
        customer_lead=customer_lead.id)

    if product_criteria == None:
        return Response("Product Criteria Doesn't Exist", status=status.HTTP_400_BAD_REQUEST)

    product_catalog_query_set = ProductCatalog.get_products_from_criteria(
        product_criteria)

    product_catalog_data = ProductCatalogSerializer(
        product_catalog_query_set, many=True).data

    product_criteria_data = ProductCriteriaSerializer(product_criteria).data

    return Response({"product_catalog": product_catalog_data, "product_criteria": product_criteria_data}, status=status.HTTP_200_OK)


@api_view(['POST'])
def select_product(request: HttpRequest) -> Response:
    """ Endpoint to capture the selected product from the customer.
        Used on Product Selection page.

    Args:
        request (HttpRequest): request triggered by customer button selection on UI

    Returns:
        Response: id and status of newly created SelectedProduct
    """
    url_token, product_catalog_id = request.data.get(
        'url_token'), request.data.get('product_catalog_id')

    customer_lead = CustomerLead.get_customer_with_url_token(url_token)
    product_catalog = ProductCatalog.objects.get(id=product_catalog_id)

    selected_product, created = SelectedProduct.objects.update_or_create(
        customer_lead=customer_lead, defaults={'product_catalog': product_catalog})

    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

    return Response(selected_product.id, status=status_code)


@api_view(['POST'])
def update_product_criteria(request: HttpRequest) -> Response:
    """ Endpoint to update the selected product criteria from the customer.
        Used on Product Selection page.

    Args:
        request (HttpRequest): request triggered by customer updates to product criteria filter on UI

    Returns:
        Response: id of updated ProductCriteria and status
    """
    product_criteria = ProductCriteria.objects.get(id=request.data.get('id'))
    product_criteria_serializer = ProductCriteriaSerializer(
        product_criteria, data=request.data, partial=True)

    if not product_criteria_serializer.is_valid():
        return Response(product_criteria_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    product_criteria = product_criteria_serializer.save()

    return Response(product_criteria.id, status=status.HTTP_200_OK)


@api_view(['POST'])
def fetch_calendly_data(request: HttpRequest) -> Response:
    """ Endpoint to get the calendly data for Customer Lead.
        Used on Scheduling page.

    Args:
        request (HttpRequest): request triggered by Calendly Listener in UI

    Returns:
        Response: id of updated ProductCriteria and status
    """
    def fetch_and_save_event(event_url, client) -> CalendlyEvent:
        scheduled_event_data = client.get(url=event_url)

        scheduled_event_serializer = CalendlyEventSerializer(
            data=scheduled_event_data.get('resource'))
        if (not scheduled_event_serializer.is_valid()):
            return Response(scheduled_event_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return scheduled_event_serializer.save()

    def fetch_and_save_invitee(invitee_url, client, calendly_event) -> CalendlyInvitee:
        calendly_invitee_data = client.get(url=invitee_url)

        calendly_invitee = calendly_invitee_data.get('resource')
        calendly_invitee['uuid'] = urlparse(
            calendly_invitee.get('uri')).path.split('/')[-1]

        invitee_serializer = CalendlyInviteeSerializer(data=calendly_invitee)
        if (not invitee_serializer.is_valid()):
            return Response(invitee_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        invitee_serializer.validated_data['event'] = calendly_event
        return invitee_serializer.save()

    def create_customer_lead_from_calendly_invitee(calendly_invitee, url_token) -> Customer:
        customer_lead = CustomerLead.get_customer_with_url_token(url_token)
        customer_lead_serializer = CustomerLeadSerializer(
            customer_lead, data={'calendly_invitee': calendly_invitee.id}, partial=True)

        if not customer_lead_serializer.is_valid():
            return Response(customer_lead_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        customer_lead_serializer.validated_data['calendly_invitee'] = calendly_invitee
        return customer_lead_serializer.save()

    def create_customer_from_lead(customer_lead, calendly_invitee) -> Customer:
        customer_data = {
            'first_name': calendly_invitee.first_name,
            'last_name': calendly_invitee.last_name,
            'email': calendly_invitee.email,
        }
        customer_serializer = CustomerSerializer(data=customer_data)

        if not customer_serializer.is_valid():
            return Response(customer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        customer_serializer.validated_data['lead'] = customer_lead
        return customer_serializer.save()

    url_token, calendly_payload = request.data.get(
        'url_token'), request.data.get('calendly_data').get('payload')

    event_url, invitee_url = calendly_payload.get(
        'event').get('uri'), calendly_payload.get('invitee').get('uri')

    calendly_client = CalendlyClient()

    calendly_event = fetch_and_save_event(
        event_url=event_url, client=calendly_client)

    calendly_invitee = fetch_and_save_invitee(
        invitee_url=invitee_url, client=calendly_client, calendly_event=calendly_event)

    customer_lead = create_customer_lead_from_calendly_invitee(
        calendly_invitee=calendly_invitee, url_token=url_token)
    customer = create_customer_from_lead(
        customer_lead=customer_lead, calendly_invitee=calendly_invitee)

    return Response(customer.id, status=status.HTTP_200_OK)


@api_view(['POST'])
def handle_reschedule_calendly_data(request: HttpRequest) -> Response:
    def remove_old_invitee(url_token, client):
        customer_lead = CustomerLead.get_customer_with_url_token(url_token)
        if customer_lead is None or customer_lead.calendly_invitee is None:
            return
        cancel_url = customer_lead.calendly_invitee.event.uri + "/cancellation"
        scheduled_event_data = client.post(url=cancel_url)
        CustomerLead.reset_calendly_invitee(url_token)
        CalendlyInvitee.remove_old_calendly_invitee(
            customer_lead.calendly_invitee.id)
        CalendlyEvent.remove_old_calendly_event(
            customer_lead.calendly_invitee.event.id)
        Customer.remove_old_customer(customer_lead.id)

    url_token = request.data.get('url_token')
    calendly_client = CalendlyClient()
    remove_old_invitee(url_token, client=calendly_client)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_customer_from_calendly_invitee(request: HttpRequest, invitee_uuid: str) -> Response:
    """ Endpoint to get the CalendlyInvitee, CustomerLead and CalendlyEvent data.
        Used on Summary page.
        invitee_uuid is from url params of Calendly redirect

    Args:
        request (HttpRequest): request triggered by Summary page load

    Returns:
        Response: CalendlyInvitee of updated ProductCriteria and status
    """

    customer = Customer.get_customer_by_invitee_uuid(uuid=invitee_uuid)

    return Response(CustomerSerializer(customer).data, status=status.HTTP_200_OK)


@api_view(['POST'])
def submit_customer_order(request: HttpRequest) -> Response:
    """ Endpoint to submit the customer order.
        Used on Summary page.

    Args:
        request (HttpRequest): request triggered by Summary page load

    Returns:
        Response: Confirmation of update and status
    """
    customer_data = request.data.get('customer')
    appointment_data = request.data.get('appointment')
    selected_product_data = request.data.get('selected_product')

    address_data = {
        "line1": customer_data.get('address'),
        "city": customer_data.get('city'),
        "state": customer_data.get('state'),
        "zip_code": customer_data.get('zip_code'),
        "gate_code": customer_data.get('gate_code'),
    }

    customer_address_serializer = CustomerAddressSerializer(data=address_data)
    if not customer_address_serializer.is_valid():
        return Response(customer_address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    customer_address = customer_address_serializer.save()

    try:
        customer = Customer.objects.get(pk=customer_data.get('id'))
        customer_serializer = CustomerSerializer(customer, data=customer_data)
    except Customer.DoesNotExist:
        customer_serializer = CustomerSerializer(data=customer_data)

    if not customer_serializer.is_valid():
        return Response(customer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    customer_serializer.validated_data['address'] = customer_address
    customer = customer_serializer.save()

    appointment_serializer = AppointmentSerializer(data=appointment_data)
    if not appointment_serializer.is_valid():
        return Response(appointment_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    appointment = appointment_serializer.save()

    job_address_serializer = JobAddressSerializer(data=address_data)
    if not job_address_serializer.is_valid():
        return Response(job_address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    job_address = job_address_serializer.save()

    job, job_created = Job.objects.update_or_create(
        customer=customer,
        appointment=appointment,
        defaults={
            'address': job_address
        }
    )

    if customer_data.get('gate_code') != "":
        job_note_text = f"GATE CODE: {customer_data.get('gate_code')}"
        JobNote.objects.create(
            job=job,
            note=job_note_text
        )

    selected_product = SelectedProduct.objects.get(
        pk=selected_product_data.get('id'))

    order, order_created = Order.objects.update_or_create(
        customer=customer,
        defaults={
            'appointment': appointment,
            'selected_product': selected_product
        }
    )

    return Response(order.id, status=status.HTTP_200_OK)
