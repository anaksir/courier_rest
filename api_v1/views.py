from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from .models import Courier
from .serializers import (
    CourierDataSerializer, CourierUpdateSerializer)


class CouriersViewSet(viewsets.ModelViewSet):
    queryset = Courier.objects.all()

    def get_serializer_class(self):
        """
        Выбор сериалайзера по действию
        """

        serializers = {
            'create': CourierDataSerializer,
            'update': CourierUpdateSerializer,
            'partial_update': CourierUpdateSerializer,
            'retrieve': CourierDataSerializer,
        }

        print(self.action)
        return serializers.get(self.action, CourierDataSerializer)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
