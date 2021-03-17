from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from .models import Courier
from .serializers import (
    CourierSerializer, CourierDataSerializer, CourierCreateSerializer
)


class CouriersViewSet(viewsets.ModelViewSet):
    queryset = Courier.objects.all()
    serializer_class = CourierCreateSerializer

    @action(methods=['post'], detail=False)
    def multiple_create(self, request):
        print(request.data)
        serializer = self.get_serializer(data=request.data['data'], many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'couriers': serializer.data}, status=status.HTTP_201_CREATED)



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
