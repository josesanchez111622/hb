import re
from typing import List, Tuple

from app.models import Customer
from booking.models import CalendlyEvent, CalendlyInvitee, ProductCatalog, ProductCriteria, SelectedProduct, TypeformResponse, Product, CustomerLead
from rest_framework import serializers

class TypeformSerializer(serializers.ModelSerializer):

    class Meta:
        model = TypeformResponse
        fields = ['form_id', 'token', 'definition', 'variables', 'hidden']

    def map_hidden(self, hidden: dict[str, any]) -> int:
        customer_lead = CustomerLead.get_customer_with_url_token(
            url_token=hidden.get('url_token'))
        if customer_lead:
            return customer_lead.id
        else:
            return None

    def map_variables(self, variables: List[dict[str, any]]) -> dict[str, any]:

        def map_variable(variable: dict[str, str]) -> Tuple[str, any]:

            def map_stair_access(value: str) -> bool:
                if value == 'no':
                    return False
                else:
                    return True

            def map_bathroom_coverage(value: str) -> int:
                return int(value[0])

            if variable.get('key') in product_criteria_model_map:
                product_criteria_type = variable.get('type')

                label = variable.get(product_criteria_type)

                if product_criteria_key == 'stair_access':
                    label = map_stair_access(label)
                elif product_criteria_key == 'bathroom_coverage':
                    label = map_bathroom_coverage(label)

                return label

        product_criteria_data = {
            'home_type': '',
            'stair_access': False,
            'bathroom_coverage': '',
            'power_type': '',
            'relocation': '',
        }

        product_criteria_model_map = {
            'home': 'home_type',
            'stairs': 'stair_access',
            'coverage': 'bathroom_coverage',
            'power': 'power_type',
            'relocation': 'relocation',
        }

        for var in variables:
            if (var.get('key') in product_criteria_model_map):
                product_criteria_key = product_criteria_model_map[var.get(
                    'key')]
                product_criteria_data[product_criteria_key] = map_variable(var)
            else:
                continue

        return product_criteria_data


class CalendlyEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendlyEvent
        fields = ['id', 'uri', 'name', 'location', 'start_time']


class CalendlyInviteeSerializer(serializers.ModelSerializer):
    event = CalendlyEventSerializer(read_only=True)

    class Meta:
        model = CalendlyInvitee
        fields = ['id', 'uri', 'uuid', 'reschedule_url', 'email',
                  'first_name', 'last_name', 'event']


class ProductCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCriteria
        fields = ['id', 'home_type', 'power_type', 'tank_type',
                  'bathroom_coverage', 'relocation', 'stair_access', 'customer_lead', 'typeform_response']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'unit_type', 'title', 'brand', 'description', 'tank_type', 'product_image', 'power_type', 'bathroom_coverages',
                  'water_flow_gpm', 'power_output_btu', 'home_coverage', ]


class ProductCatalogSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductCatalog
        fields = ['id', 'home_types', 'current_location', 'desired_location',
                  'is_popular', 'base_price', 'warranty', 'total_rebates', 'socal_gas_rebates',
                  'federal_tax_credit', 'product', 'final_price', 'installation_price', 'stair_price']


class SelectedProductSerializer(serializers.ModelSerializer):
    product_catalog = ProductCatalogSerializer(read_only=True)

    class Meta:
        model = SelectedProduct
        fields = ['id', 'product_catalog', 'customer_lead']


class CustomerLeadSerializer(serializers.ModelSerializer):
    calendly_invitee = CalendlyInviteeSerializer(read_only=True)
    product_criteria = ProductCriteriaSerializer(read_only=True)
    selected_product = SelectedProductSerializer(read_only=True)

    class Meta:
        model = CustomerLead
        fields = ['id', 'url_token', 'calendly_invitee',
                  'product_criteria', 'selected_product']
