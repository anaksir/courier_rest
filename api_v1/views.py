from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from .models import Courier
from .serializers import (
    CourierDataSerializer, CourierCreateSerializer,
    CourierUpdateSerializer, TestCustomRelatedCourierUpdateSerializer
)

from .models import Item
from .serializers import ItemDataSerializer


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
            'retrieve': CourierUpdateSerializer,
        }

        print(self.action)
        return serializers.get(self.action, CourierDataSerializer)

    # @action(methods=['post'], detail=False)
    # def multiple_create(self, request):
    #     print(request.data)
    #     serializer = self.get_serializer(data=request.data['data'], many=True)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     return Response({'couriers': serializer.data}, status=status.HTTP_201_CREATED)

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

        data_errors = serializer.errors.get('data')
        print(data_errors)
        if isinstance(data_errors[0], dict):
            invalid_ids = [err for err in data_errors if err]
            error_response = {
                'validation_error': {
                    'couriers': invalid_ids
                }
            }
        else:
            error_response = serializer.errors

        return Response(
            error_response,
            status=status.HTTP_400_BAD_REQUEST,
        )


class NewCouriers(CreateAPIView):
    queryset = Courier.objects.all()
    serializer_class = CourierCreateSerializer
    #
    # def perform_create(self, serializer):
    #     if self.request.data.get('image') is not None:
    #         product_image = self.request.data.get('image')
    #         serializer.save(owner=owner,product_image=product_image)
    #     else:
    #         serializer.save(owner=owner)
    #
    # def post(self, request):
    #     couriers_raw_data = request.data.get('data')
    #     serializer = CourierCreateSerializer(data=couriers_raw_data, many=True)
    #     if serializer.is_valid(raise_exception=True):
    #         print('OK')
    #     return Response({"success": "Article '{}' created successfully"})


@api_view()
def couriers(request):
    return Response({"message": "Hello, world!"})


class ItemsViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemDataSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        print(serializer.errors)
        # Delete empty error dicts from list
        error_response = [error_id for error_id in
                          serializer.errors['items_data'] if error_id]
        return Response(
            {'errors': error_response},
            status=status.HTTP_400_BAD_REQUEST
        )
