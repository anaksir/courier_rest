from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status
from .models import Courier, Order
from .serializers import (
    CourierDataSerializer, CourierUpdateSerializer, OrderDataSerializer,
    OrderAssignSerializer, CompleteOrderSerializer, CourierInfoSerializer,
    )


def _form_validations_response(serializer, request, model):
    """
    Костыль для того, чтобы в случае ошибок валидации вернуть id с
    некорректными данными.
    """
    unvalidated_ids = []
    validations_errors = serializer.errors.get('data')
    for i, error in enumerate(validations_errors):
        if error and isinstance(error, dict):
            try:
                wrong_id = request.data['data'][i][f'{model}_id']
                unvalidated_ids.append({'id': wrong_id})
            except (KeyError, TypeError):
                unvalidated_ids = 'incorrect data'
    error_response = {'validation_error': {f'{model}s': unvalidated_ids}}
    return Response(error_response, status=status.HTTP_400_BAD_REQUEST)


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
        """
        Создает курьеров из списка, переданного в ключе "data".
        Возвращает словарь, по ключу "couriers" находится список словарей с id
        созданных курьеров.
        В случае ошибок валидации вернет id курьеров с ошибочным данными.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )

        return _form_validations_response(serializer, request, 'courier')


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
        """
        Создает заказы из списка, переданного в ключе "data".
        Возвращает словарь, по ключу "orders" находится список словарей с id
        созданных заказов.
        В случае ошибок валидации вернет id заказов с ошибочным данными.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )

        return _form_validations_response(serializer, request, 'order')

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
