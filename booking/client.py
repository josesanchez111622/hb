import requests
from django.conf import settings


class CalendlyClient(object):
    def get_header(self):
        return {'Authorization': f"Bearer {settings.CALENDLY_API_KEY}",'Content-Type': 'application/json'}

    def get(self, url):
        headers = self.get_header()
        response=requests.get(url, headers=headers)
        return response.json()

    def post(self, url):
        headers = self.get_header()
        response = requests.post(url, headers=headers)
        return response.json()