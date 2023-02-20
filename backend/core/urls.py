from django.urls import path

from .views import (
    WarmUpView,
)

urlpatterns = [
    path("_ah/warmup", WarmUpView.as_view()),
]
