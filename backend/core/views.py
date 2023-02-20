from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class WarmUpView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(status=status.HTTP_204_NO_CONTENT)
