from __future__ import annotations

from rest_framework import serializers

from accounts.models import (
    CustomUser,
)


class CustomUserSerializer(serializers.ModelSerializer[CustomUser]):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "last_login",
            "is_superuser",
            "username",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
            "date_joined",
            "email",
            "phone",
            "timezone",
        ]
