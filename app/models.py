from __future__ import annotations
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from libcst import Add
from app.helper.slack import post_to_customers_and_active_jobs, post_to_boom
import auto_prefetch
import pytz
from ckeditor.fields import RichTextField
from django.core.validators import FileExtensionValidator
from booking.models import CustomerLead
from simple_history.models import HistoricalRecords
import hashlib
import analytics


class Address(auto_prefetch.Model):
    owner = auto_prefetch.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=30)
    country = models.CharField(max_length=255, default="US")
    gate_code = models.CharField(max_length=255, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.id} {self.line1} {self.line2} {self.city} {self.state} {self.country}"


class CustomerAddress(Address):
    pass


class JobAddress(Address):
    pass


class SupplyHouseAddress(Address):
    pass


class ProBusinessAddress(Address):
    pass


class Customer(auto_prefetch.Model):
    user = auto_prefetch.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    address = auto_prefetch.ForeignKey(
        CustomerAddress, on_delete=models.CASCADE, null=True)
    lead = auto_prefetch.ForeignKey(CustomerLead, null=True,
                                    blank=True, on_delete=models.CASCADE)
    email = models.EmailField(_('email address'), blank=True)
    history = HistoricalRecords()

    def get_customer_by_invitee_uuid(uuid):
        return Customer.objects.filter(lead__calendly_invitee__uuid=uuid).first()

    def get_customer_with_url_token(url_token):
        return Customer.objects.filter(url_token=url_token).first()

    def remove_old_customer(lead_id):
        Customer.objects.filter(lead=lead_id).delete()

    def __str__(self):
        return f"{self.id} {self.first_name} {self.last_name} {self.address}"

    def __identify__(self):
        return {
            'firstName': self.first_name,
            'lastName': self.last_name,
            'phone': self.phone,
            'address': str(self.address) if self.address else None,
            'gateCode': self.address.gate_code if self.address else None,
            'lead': self.lead.id,
            'email': self.email,
        }


@receiver(post_save, sender=Customer, dispatch_uid="emit_identify_to_segment")
def post_customer_saved(sender, instance, created, update_fields, **kwargs):
    if not instance.lead:
        return

    analytics.identify(
        anonymous_id=instance.lead.url_token,
        user_id=instance.id,
        traits=instance.__identify__()
    )


def customer_photo_path(instance, filename):
    directory_name = f'customer-photo-{instance.customer.pk}'.encode('utf-8')
    return f"uploads/{hashlib.shake_256(directory_name).hexdigest(10)}/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{filename}"


class CustomerPhoto(auto_prefetch.Model):
    customer = auto_prefetch.ForeignKey(Customer, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to=customer_photo_path)


class ProBusiness(auto_prefetch.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    owner = auto_prefetch.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True)
    address = auto_prefetch.ForeignKey(ProBusinessAddress, on_delete=models.CASCADE, null=True)
    url = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(
        upload_to="pro_business_logos/", null=True, blank=True)
    history = HistoricalRecords()

    def get_pro_business_by_user_id(user_id):
        return ProBusiness.objects.filter(pro__user__id=user_id).first()

    def __str__(self):
        return f"{self.id} {self.name} {self.owner}"

class Pro(auto_prefetch.Model):
    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, null=True)
    business = auto_prefetch.ForeignKey(ProBusiness, on_delete=models.CASCADE)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.id} {self.user.first_name} {self.user.last_name} {self.business.name} {self.user.phone}"

    def get_pro_user(user):
        return Pro.objects.filter(user=user).first()

class Appointment(auto_prefetch.Model):
    date = models.DateTimeField(default=timezone.now)
    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.id} {self.date}"

class JobTypeArchetype(models.TextChoices):
    TANK_INSTALLATION = "Tank Installation", _("Tank")
    TANKLESS_INSTALLATION = "Tankless Installation", _("Tankless")


class JobType(auto_prefetch.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=255, choices=JobTypeArchetype.choices, default=JobTypeArchetype.TANK_INSTALLATION)
    scope = RichTextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

class Job(auto_prefetch.Model):
    customer = auto_prefetch.ForeignKey(Customer, on_delete=models.CASCADE)
    address = auto_prefetch.ForeignKey(JobAddress, on_delete=models.CASCADE, null=True)
    pro_business = auto_prefetch.ForeignKey(
        ProBusiness, on_delete=models.CASCADE, null=True)
    type = auto_prefetch.ForeignKey(
        JobType, on_delete=models.CASCADE, null=True)
    appointment = auto_prefetch.ForeignKey(
        Appointment, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    scope = RichTextField(blank=True, null=True)
    is_customer_confirmed = models.BooleanField(default=False)
    is_customer_email_confirmation_sent = models.BooleanField(default=False)
    is_plumber_confirmed = models.BooleanField(default=False)
    is_parts_ordered = models.BooleanField(default=False)
    is_plumber_details_sent = models.BooleanField(default=False)
    is_job_customer_approved = models.BooleanField(default=False)
    is_payment_received = models.BooleanField(default=False)
    is_warranty_info_sent = models.BooleanField(default=False)
    is_customer_review_requested = models.BooleanField(default=False)
    is_hb_approved = models.BooleanField(default=False)
    is_started = models.BooleanField(default=False)
    is_pro_finished = models.BooleanField(default=False)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.id} - {self.customer.first_name} {self.customer.last_name} @ {self.address.city} - {self.type} - {self.pro_business.name if self.pro_business else 'None'}"

    @staticmethod
    def get_all_completed(user_id: int = 0) -> QuerySet[Job]:
        queryset = (
            Job.objects
            .select_related("type")
            .filter(is_pro_finished=True)
            .order_by("appointment__date")
        )

        if user_id != 0:
            queryset = queryset.filter(pro_business__pro__user__id=user_id)

        return queryset

    @staticmethod
    def get_all_open(user_id: int = 0) -> QuerySet[Job]:
        queryset = (
            Job.objects
            .select_related(
                "type",
                "address",
                "pro_business",
                "appointment",
            )
            .prefetch_related(
                "material_list",
            )
            .filter(is_pro_finished=False)
            .order_by("appointment__date")
        )

        if user_id != 0:
            queryset = queryset.filter(pro_business__pro__user__id=user_id)

        return queryset

    @staticmethod
    def get_details(pk: int, user_id: int = 0) -> Job:
        queryset = Job.objects.select_related(
            "type",
            "address",
            "appointment",
        )

        if user_id != 0:
            queryset = queryset.filter(pro_business__pro__user__id=user_id)

        return queryset.get(pk=pk)

    def has_photos(self):
        return JobPhoto.objects.filter(job=self).exists()

    def completion_date(self) -> str:
        try:
            return str(self.history.filter(Q(id=self.id) & Q(is_pro_finished=True)).order_by("id").first().history_date.replace(tzinfo=None))
        except:
            return str(datetime.now().replace(tzinfo=None))

    def is_completed(self) -> bool:
        return self.is_pro_finished

    def complete(self) -> None:
        if self.is_completed():
            return

        self.is_pro_finished = True
        self.is_started = True
        self.save(update_fields=['is_pro_finished', 'is_started'])


@receiver(post_save, sender=Job, dispatch_uid="post_job_to_slack")
def post_job_saved(sender, instance, created, update_fields, **kwargs):
    date = datetime.now(tz=pytz.timezone("US/Pacific"))
    if(update_fields is None or ("is_pro_finished" not in update_fields) or instance.is_pro_finished == False):
        return
    job_link = f"{settings.ADMIN_URL}app/sadmin/app/job/{instance.pk}/change/"
    message = (
        f"{instance.pro_business.name} marked Job #{instance.id} as complete at {date.strftime('%I:%M%p %Z %B %d, %Y')}\n"
        f"{instance.type}\n"
        f"{instance.address}\n"
        f"{job_link}"
    )
    post_to_customers_and_active_jobs(text=message)

class JobIssue(auto_prefetch.Model):
    class IssueType(models.TextChoices):
        Misc = 1, _("Misc")
        ScopingError = (
            2,
            _("Scoping Error"),
        )
        Parts = 3, _("Parts")
        Timeliness = 4, _("Timeliness")
        OnSiteDamage = 5, _("On-Site Damage")

    user = auto_prefetch.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True)
    job = auto_prefetch.ForeignKey(Job, on_delete=models.CASCADE)
    issue = models.IntegerField(choices=IssueType.choices)
    notes = models.TextField(max_length=255, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    history = HistoricalRecords()


@receiver(post_save, sender=JobIssue, dispatch_uid="post_job_issue_to_slack")
def post_job_issue_saved(sender, instance, created, **kwargs):
    if created is False:
        return

    issue_link = f"{settings.ADMIN_URL}app/sadmin/app/jobissue/{instance.pk}/change/"
    message = (
        f"{instance.user} reported an issue on Job #{instance.job}:\n"
        f"{JobIssue.IssueType(instance.issue).label}\n\n"
        f"{instance.notes}\n\n"
        f"{issue_link}"
    )
    post_to_customers_and_active_jobs(text=message)


class JobNote(auto_prefetch.Model):
    note = RichTextField(blank=True, null=True)
    job = auto_prefetch.ForeignKey(
        Job, on_delete=models.CASCADE, related_name='job_notes')
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.id} {self.note}"

def job_photo_path(instance, filename):
    directory_name = f'job-photo-{instance.job.pk}'.encode('utf-8')
    return f"uploads/{hashlib.shake_256(directory_name).hexdigest(10)}/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{filename}"


class JobPhoto(auto_prefetch.Model):
    job = auto_prefetch.ForeignKey(Job, on_delete=models.CASCADE,
                                   related_name='job_photos')
    photo = models.ImageField(upload_to=job_photo_path)

    def __str__(self) -> str:
        return f"id: {self.id} job: {self.job}"

    def add_photo(job, photo):
        return JobPhoto.objects.create(job=job, photo=photo)

    def get_photos(job):
        return JobPhoto.objects.filter(job=job).all()

    def remove_photo_by_id(photoId):
        JobPhoto.objects.filter(id=photoId).delete()

    def thumbnail(self):
        if self.photo != '':
            return mark_safe('<img src="%s%s" width="150" height="150" />' % (f'{settings.GCP_BASE_URL}', self.photo))


def post_news_photos(new_photo_urls, job=Job):
    photo_links = "\n".join(new_photo_urls)
    date = datetime.now(tz=pytz.timezone("US/Pacific"))
    job_link = f"{settings.ADMIN_URL}app/sadmin/app/job/{job.pk}/change/"
    message = (
        f"{job.pro_business.name} uploaded photos to Job #{job.id} as complete at {date.strftime('%I:%M%p %Z %B %d, %Y')}\n"
        f"{job.type}\n"
        f"{job.address}\n"
        f"{job_link}\n"
        f"First three photos attached:\n"
        f"{photo_links}"
    )
    post_to_customers_and_active_jobs(text=message)

class SupplyHouse(auto_prefetch.Model):
    brand = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    owner = auto_prefetch.ForeignKey(
        get_user_model(), default=None, null=True, on_delete=models.CASCADE
    )
    address = auto_prefetch.ForeignKey(
        SupplyHouseAddress, on_delete=models.CASCADE, null=True)
    url = models.CharField(max_length=255, null=True)
    logo = models.ImageField(
        upload_to="supplier_logos/", blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"id: {self.id} name: {self.name} address: {self.address}"

def order_receipt_path(instance, filename):
    directory_name = f'order-receipt-{instance.job.pk}'.encode('utf-8')
    return f"uploads/{hashlib.shake_256(directory_name).hexdigest(10)}/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{filename}"

class MaterialList(auto_prefetch.Model):
    order_number = models.CharField(max_length=255, blank=True)
    job = auto_prefetch.ForeignKey(Job, on_delete=models.CASCADE, related_name="material_list")
    supply_house = auto_prefetch.ForeignKey(
        SupplyHouse, on_delete=models.CASCADE, null=True, related_name="supply_house")
    receipt = models.FileField(upload_to=order_receipt_path, blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=["pdf"])])

    def __str__(self) -> str:
        return f"id: {self.id} job: {self.job} supply house: {self.supply_house}"

class  MaterialListIssue(auto_prefetch.Model):
    note = models.TextField()
    material_list = auto_prefetch.ForeignKey(MaterialList, on_delete=models.CASCADE,  null=True)
    date = models.DateTimeField(default=timezone.now)
    user = auto_prefetch.ForeignKey(get_user_model(), on_delete=models.CASCADE)
