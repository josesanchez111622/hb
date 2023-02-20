import uuid
import auto_prefetch
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _
from django.db.models import JSONField
from simple_history.models import HistoricalRecords

from django.db.models.signals import post_save
from django.dispatch import receiver
import pytz
from datetime import datetime
from app.helper.slack import post_to_boom


class TypeformResponse(auto_prefetch.Model):
    form_id = models.TextField()
    token = models.TextField()
    definition = JSONField()
    variables = JSONField()
    hidden = JSONField()


class CalendlyEvent(auto_prefetch.Model):
    uri = models.TextField()
    name = models.TextField()
    start_time = models.DateTimeField()
    location = JSONField()

    @classmethod
    def remove_old_calendly_event(cls, id):
        cls.objects.filter(id=id).delete()


class CalendlyInvitee(auto_prefetch.Model):
    uri = models.TextField()
    uuid = models.TextField()
    reschedule_url = models.TextField()
    email = models.TextField()
    first_name = models.TextField()
    last_name = models.TextField()

    event = auto_prefetch.ForeignKey(
        CalendlyEvent, on_delete=models.CASCADE)

    @classmethod
    def remove_old_calendly_invitee(cls, id):
        cls.objects.filter(id=id).delete()


def customer_url_token_default_function():
    return str(uuid.uuid4())


class CustomerLead(auto_prefetch.Model):
    url_token = models.TextField(
        default=customer_url_token_default_function, unique=True)

    calendly_invitee = auto_prefetch.ForeignKey(
        CalendlyInvitee, on_delete=models.CASCADE, null=True, blank=True)
    typeform_response = auto_prefetch.ForeignKey(
        TypeformResponse, on_delete=models.CASCADE, null=True, blank=True)

    @classmethod
    def get_customer_with_url_token(cls, url_token):
        return cls.objects.filter(url_token=url_token).first()

    @classmethod
    def reset_calendly_invitee(cls, url_token):
        customer_lead = cls.get_customer_with_url_token(url_token)
        customer_lead.calendly_invitee = None
        customer_lead.save()


class TankType(models.TextChoices):
    Tank = "tank", _("Tank Water Heater")
    Tankless = "tankless", _("Tankless Water Heater")


class HomeType(models.TextChoices):
    SINGLE_FAMILY = "single_family", _("Single Family")
    TOWNHOME = "townhome", _("Townhome")
    CONDO = "condo", _("Condo")
    MANUFACTURED = "manufactured", _("Manufactured")


class PowerType(models.TextChoices):
    GAS = "gas", _("Gas")
    ELECTRIC = "electric", _("Electric")
    PROPANE = "propane", _("Propane")


class BathroomCoverage(models.IntegerChoices):
    ONE = 1, _("1 bathroom")
    TWO = 2,  _("2 bathrooms")
    THREE = 3, _("3 bathrooms")
    FOURORMORE = 4, _("4+ bathrooms")


class Relocation(models.TextChoices):
    NONE = "current", _("Current Location")
    INDOOR_CLOSEST = "indoor_closet", _("Indoor Closet")
    BASEMENGT = "basement", _("Basement")
    OUTDOOR_LESS_THAN_10_FEET = "outdoor_within_10_feet",  _(
        "Outdoor within 10 feet of gas mainline")
    OUTDOOR_MORE_THAN_10_FEET = "outdoor_over_10_feet", _(
        "Outdoor over 10 feet from gas mainline")
    GARAGE = "garage", _("Garage")


def get_bathroom_coverages_default():
    return list(BathroomCoverage.ONE, BathroomCoverage.TWO)


class Product(auto_prefetch.Model):
    unit_type = models.CharField(
        max_length=255, default="")
    title = models.CharField(max_length=255, default="", unique=True,)
    brand = models.CharField(max_length=255, default="")
    description = models.TextField()
    tank_type = models.CharField(
        max_length=255, choices=TankType.choices, default=TankType.Tank)
    product_image = models.TextField(blank=True, null=True)
    power_type = models.CharField(
        max_length=255, choices=PowerType.choices, default=PowerType.GAS)
    bathroom_coverages = ArrayField(models.IntegerField(
        choices=BathroomCoverage.choices,
        default=BathroomCoverage.ONE),
        default=get_bathroom_coverages_default)
    water_flow_gpm = models.CharField(
        max_length=255, blank=True, null=True)
    power_output_btu = models.CharField(
        max_length=255, blank=True, null=True)
    home_coverage = models.CharField(max_length=255)
    history = HistoricalRecords()


# ProductCatalog includes any variable associated with price/value of a product
class ProductCatalog(auto_prefetch.Model):
    home_types = ArrayField(models.CharField(
        max_length=255, choices=HomeType.choices))
    current_location = models.CharField(
        max_length=255, choices=Relocation.choices, default=Relocation.NONE)
    desired_location = models.CharField(
        max_length=255, choices=Relocation.choices, default=Relocation.NONE)
    is_popular = models.BooleanField(default=False)
    base_price = models.IntegerField(default=0)
    stair_price = models.IntegerField(default=0)
    warranty = models.IntegerField(default=0)
    total_rebates = models.IntegerField(default=0)
    socal_gas_rebates = models.IntegerField(blank=True, null=True)
    federal_tax_credit = models.IntegerField(blank=True, null=True)
    product = auto_prefetch.ForeignKey(
        Product, on_delete=models.CASCADE, null=True)
    history = HistoricalRecords()

    def relocation(self):
        if self.current_location == self.desired_location:
            return Relocation.NONE
        else:
            return self.desired_location

    def installation_price(self):
        return self.base_price + self.stair_price

    def final_price(self):
        return self.base_price - self.total_rebates + self.stair_price

    @classmethod
    def get_products_from_criteria(cls, product_criteria):
        queryset = cls.objects
        desired_location = models.F('current_location')
        if product_criteria.relocation != Relocation.NONE:
            desired_location = product_criteria.relocation
            queryset = queryset.exclude(current_location=desired_location)

        product_catalog_query_set = queryset.filter(
            home_types__contains=[product_criteria.home_type],
            product__power_type=product_criteria.power_type,
            product__tank_type=product_criteria.tank_type,
            product__bathroom_coverages__contains=[
                product_criteria.bathroom_coverage],
            desired_location=desired_location,
            stair_price=product_criteria.stair_access*100
        ).all().distinct('product')

        return sorted(product_catalog_query_set,
                      key=lambda product: (-product.is_popular, product.final_price()))


class ProductCriteria(auto_prefetch.Model):
    home_type = models.TextField(
        choices=HomeType.choices, default=HomeType.SINGLE_FAMILY)
    power_type = models.TextField(
        choices=PowerType.choices, default=PowerType.GAS)
    bathroom_coverage = models.IntegerField(
        choices=BathroomCoverage.choices, default=BathroomCoverage.ONE)
    relocation = models.TextField(
        blank=True, choices=Relocation.choices, default=Relocation.NONE)
    stair_access = models.BooleanField(default=False)
    tank_type = models.CharField(
        max_length=255, choices=TankType.choices, default=TankType.Tankless)

    typeform_response = models.OneToOneField(
        TypeformResponse, on_delete=models.CASCADE, null=True)
    customer_lead = models.OneToOneField(
        CustomerLead, on_delete=models.CASCADE, null=True, related_name="product_criteria")
    history = HistoricalRecords()

    def get_criteria_with_customer_lead(customer_lead):
        return ProductCriteria.objects.filter(customer_lead=customer_lead).first()


class SelectedProduct(auto_prefetch.Model):
    product_catalog = auto_prefetch.ForeignKey(
        ProductCatalog, on_delete=models.CASCADE, null=True)
    customer_lead = models.OneToOneField(
        CustomerLead, on_delete=models.CASCADE, null=True, related_name="selected_product")
    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.product_catalog.product.title}"


class OrderStatus(models.TextChoices):
    Ordered = "ORDERED", _("Ordered")
    Approved = "APPROVED", _("Approved")
    JobQueued = "QUEUED", _("Job Queued"),
    Paid = "PAID", _("Paid")


class Order(auto_prefetch.Model):
    customer = auto_prefetch.ForeignKey(
        'app.Customer', on_delete=models.CASCADE)
    selected_product = auto_prefetch.ForeignKey(
        SelectedProduct, on_delete=models.CASCADE)
    appointment = auto_prefetch.ForeignKey(
        'app.Appointment', on_delete=models.CASCADE)
    order_status = models.CharField(
        max_length=8, choices=OrderStatus.choices, default=OrderStatus.Ordered)
    history = HistoricalRecords()


@receiver(post_save, sender=Order, dispatch_uid="post_order_to_slack")
def post_order_saved(sender, instance, created, update_fields, **kwargs):
    date = datetime.now(tz=pytz.timezone("US/Pacific"))
    if not created:
        return
    message = (
        f"New online booking!\n"
        f"{date.strftime('%I:%M%p %Z %B %d, %Y')}\n"
        f"{instance.selected_product.product_catalog.product.title}\n"
        f"{'${:,.2f}'.format(instance.selected_product.product_catalog.final_price())}\n"
        f"{instance.customer.address}\n"
        f"{instance.customer.first_name} {instance.customer.last_name}\n"
        f"{instance.customer.email}\n"
        f"{instance.customer.phone}\n"
    )
    post_to_boom(text=message)
