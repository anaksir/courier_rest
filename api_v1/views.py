from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status
from .models import Courier, Order
from .serializers import (
    CourierDataSerializer, CourierUpdateSerializer, OrderDataSerializer,
    OrderAssignSerializer, CompleteOrderSerializer, CourierInfoSerializer,
    )


class CouriersViewSet(viewsets.ModelViewSet):
    queryset = Courier.objects.all()
    http_method_names = ['post', 'patch', 'get']

    def get_serializer_class(self):
        """
        Выбор сериалайзера по действию
        """

        serializers = {
            'create': CourierDataSerializer,
            'update': CourierUpdateSerializer,
            'partial_update': CourierUpdateSerializer,
            'retrieve': CourierInfoSerializer,
        }

        return serializers.get(self.action, CourierDataSerializer)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )

        unvalidated_ids = []
        validations_errors = serializer.errors.get('data')
        for i, error in enumerate(validations_errors):
            if error and isinstance(error, dict):
                try:
                    wrong_id = request.data['data'][i]['courier_id']
                except KeyError:
                    wrong_id = 'no courier_id was passed '
                unvalidated_ids.append({'id': wrong_id})
        error_response = {'validation_error': {'couriers': unvalidated_ids}}
        return Response(error_response, status=status.HTTP_400_BAD_REQUEST,)


class OrdersViewSet(viewsets.ModelViewSet):
    http_method_names = ['post']
    queryset = Order.objects.all()
    serializer_class = OrderDataSerializer

    def get_serializer_class(self):
        """
        Выбор сериалайзера по действию
        """
        serializers = {
            'create': OrderDataSerializer,
            'assign': OrderAssignSerializer,
            'complete': CompleteOrderSerializer,
        }

        return serializers.get(self.action, OrderDataSerializer)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )

        unvalidated_ids = []
        validations_errors = serializer.errors.get('data')
        for i, error in enumerate(validations_errors):
            if error and isinstance(error, dict):
                try:
                    wrong_id = request.data['data'][i]['order_id']
                except KeyError:
                    wrong_id = 'no order_id was passed '
                unvalidated_ids.append({'id': wrong_id})
        error_response = {'validation_error': {'orders': unvalidated_ids}}
        return Response(error_response, status=status.HTTP_400_BAD_REQUEST,)

    @action(methods=['post'], detail=False)
    def assign(self, request, *args, **kwargs):
        """
        Endpoint для назначения курьеру подходящих заказов
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
                headers=headers
            )

    @action(methods=['post'], detail=False)
    def complete(self, request):
        """
        Endpoint для отметки о выполнении заказа
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
                headers=headers
            )
