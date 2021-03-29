from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from api_v1.models import Courier, Order, Region, TimeInterval


class AssignTests(APITestCase):
    """
    Тест назначения курьеру заказов
    """
    def setUp(self):
        courier_data = {
            'courier_id': 1,
            'courier_type': "foot",
            'regions': [1, 12, 22],
            'working_hours': ['09:00-14:00', '17:00-22:00']
        }
        region_data = courier_data.pop('regions')
        working_hours_data = courier_data.pop('working_hours')
        regions = Region.objects.bulk_create(
            [Region(region_id=i) for i in region_data]
        )
        working_hours = [
            TimeInterval.objects.create(interval=i) for i in working_hours_data
        ]
        self.courier = Courier.objects.create(**courier_data)
        self.courier.regions.set(regions)
        self.courier.working_hours.set(working_hours)

        hours = ['08:00-12:00', '15:00-16:00', '18:00-23:00']
        intervals = [
            TimeInterval.objects.create(interval=i) for i in hours
        ]

        self.order_1 = Order.objects.create(
            id=1,
            weight=9,
            region=regions[0],
        )
        self.order_1.delivery_hours.set([intervals[0]])
        self.order_2 = Order.objects.create(
            id=2,
            weight=12,
            region=regions[1],
        )
        self.order_2.delivery_hours.set([intervals[1]])
        self.order_3 = Order.objects.create(
            id=3,
            weight=9,
            region=regions[2],
        )
        self.order_3.delivery_hours.set([intervals[2]])
        self.data = {'courier_id': 1}
        self.success_data = [{"id": 1}, {"id": 3}]
        self.invalid_data = {'courier_id': 999}

    def test_assign_orders(self):
        """
        Проверка назначения заказов курьеру
        """
        url = reverse('orders-assign')
        response = self.client.post(url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['orders'], self.success_data)

    def test_wrong_courier_id(self):
        """
        Проверка ответа при передаче несуществующего id курьера
        """
        url = reverse('orders-assign')
        response = self.client.post(url, self.invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
