from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets
from .models import Courier
from .serializers import CourierSerializer, CourierDataSerializer


class CouriersViewSet(viewsets.ModelViewSet):
    queryset = Courier.objects.all()
    serializer_class = CourierDataSerializer
    http_method_names = ('post',)


@api_view()
def couriers(request):
    return Response({"message": "Hello, world!"})
