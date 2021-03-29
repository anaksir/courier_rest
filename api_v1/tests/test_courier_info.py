from datetime import datetime
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from api_v1.models import Courier, Order, AssignedOrder, Region, TimeInterval


class CompleteTests(APITestCase):
    """
    Тест выполнения курьером заказа
    """
    def setUp(self):
        courier_data = {
            'courier_id': 1,
            'courier_type': 'foot',
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
        courier = Courier.objects.create(**courier_data)
        courier.regions.set(regions)
        courier.working_hours.set(working_hours)

        hours = ['08:00-12:00', '15:00-16:00', '18:00-23:00']
        intervals = [
            TimeInterval.objects.create(interval=i) for i in hours
        ]

        order_1 = Order.objects.create(
            id=1,
            weight=9,
            region=regions[0],
        )
        order_1.delivery_hours.set([intervals[0]])
        order_2 = Order.objects.create(
            id=2,
            weight=12,
            region=regions[1],
        )
        order_2.delivery_hours.set([intervals[1]])
        order_3 = Order.objects.create(
            id=3,
            weight=9,
            region=regions[2],
        )
        order_3.delivery_hours.set([intervals[2]])
        assign_time = datetime.fromisoformat('2021-03-29T14:30:01.161978')
        complete_time = datetime.fromisoformat('2021-03-29T14:45:00.161978')
        AssignedOrder.objects.create(
            courier=courier,
            order=order_1,
            assign_time=assign_time,
            complete_time=complete_time,
            is_competed=True,
            payment=1000,
            delivery_time=complete_time - assign_time
        )

        self.valid_response = {
            'courier_id': 1,
            'courier_type': 'foot',
            'regions': [1, 12, 22],
            'working_hours': ['09:00-14:00', '17:00-22:00'],
            'rating': 3.75,
            'earnings': 1000
        }

    def test_assign_orders(self):
        """
        Проверка назначения заказов курьеру
        """
        url = reverse('couriers-detail', args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.valid_response)

    def test_invalid_data(self):
        """
        Проверка ответа при передаче невалидных данных
        """
        url = reverse('couriers-detail', args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
