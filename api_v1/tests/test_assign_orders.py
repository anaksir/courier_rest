from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response
from api_v1.models import Courier, Order, AssignedOrder, Region, TimeInterval


class AssignTests(APITestCase):
    def test_invalid_update(self):
        """
        Проверка назначения заказов курьеру
        """
        courier_data = {
            "courier_id": 2,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
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

        orders_data = {'data': [
            {
                "order_id": 1,
                "weight": 9,
                "region": 1,
                "delivery_hours": ["09:00-16:00"]
            },
            {
                "order_id": 2,
                "weight": 5,
                "region": 12,
                "delivery_hours": ["16:00-19:00"]
            },
            {
                "order_id": 3,
                "weight": 1,
                "region": 22,
                "delivery_hours": ["07:00-12:00"]
            },
        ]}
        self.client.post(reverse('orders-list'), orders_data, format='json')
        url = reverse('orders-assign')
        data = {'courier_id': 2}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        success_data = [{"id": 1}, {"id": 3}]
        self.assertEqual(response.data['orders'], success_data)
        print(response.data)
        print('-'*80)
        # # Проверка на идемпотентность:
        # response2 = self.client.post(url, data, format='json')
        # self.assertEqual(response2.data['orders'], success_data)
        # print(response2.data)
