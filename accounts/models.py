from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.fields.files import ImageField
import pyotp
import phonenumbers

class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'))
    phone = models.CharField(max_length=255, unique=True)
    image = ImageField(upload_to="profile_pics", blank=True, null=True)
    timezone = models.CharField(max_length=50, default="US/Pacific")
    sms_key = models.CharField(max_length=100, blank=True)
    REQUIRED_FIELDS = ['phone', 'email']

    def clean(self):
        super().clean()
        try:
            parsed_number = phonenumbers.parse(self.phone, "US")
        except:
            raise ValidationError("Invalid Phone Number")
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValidationError("Invalid Phone Number")

    def save(self, *args, **kwargs):
        parsed_number = phonenumbers.parse(self.phone, "US")
        self.phone = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        super().save(*args, **kwargs)

    def is_pro(self):
        return self.groups.filter(name="pro").exists()

    def __str__(self):
        return self.email

    def get_custom_user_with_number(number):
        return CustomUser.objects.filter(phone=number).first()

    def generate_key(self):
        key = pyotp.random_base32()
        if self.is_unique_by_sms(key):
            self.sms_key = key
            self.save()
            return key
        return self.generate_key()

    def is_unique_by_sms(self, key):
        try:
            CustomUser.objects.get(sms_key=key)
        except CustomUser.DoesNotExist:
            return True
        return False
