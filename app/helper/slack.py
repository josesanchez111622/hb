import requests
from django.conf import settings


def post_to_customers_and_active_jobs(text):
    return requests.post(
        settings.SLACK_CUSTOMER_AND_JOBS_WEBHOOK,
        json={"text": text},
    )

def post_to_boom(text):
    return requests.post(
        settings.SLACK_BOOM,
        json={"text": text},
    )