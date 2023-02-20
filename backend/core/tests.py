from rest_framework import status
from rest_framework.test import APITransactionTestCase


class WarmUpTests(APITransactionTestCase):
    def test_warmup(self):
        response = self.client.get("/_ah/warmup")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
