from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response
from api_v1.models import Courier, TimeInterval, Region


class CouriersTests(APITestCase):
    """
    Проверка обновления информации о курьере.
    """
    def setUp(self):
        working_hours = ['09:00-14:00', '15:00-22:00']
        intervals = [
            TimeInterval.objects.create(interval=i) for i in working_hours
        ]
        region_ids = [1, 12, 22]
        regions = [
            Region.objects.create(region_id=i) for i in region_ids
        ]
        self.courier = Courier.objects.create(
            courier_id=1,
            courier_type='foot'
        )
        self.courier.working_hours.set(intervals)
        self.courier.regions.set(regions)

        self.update_data = {
            "courier_type": "car",
            "regions": [13],
        }
        self.valid_response = {
            'courier_id': 1,
            'courier_type': 'car',
            'working_hours': ['09:00-14:00', '15:00-22:00'],
            'regions': [13]
        }
        self.invalid_update_data = {
            'courier_type': 'car',
            'regions': [13],
            'Foo': 'Bar'
        }

    def test_update_courier(self):
        """
        Проверка валидного обновления.
        """
        update_url = reverse('couriers-detail', args=[1])
        response = self.client.patch(
            update_url,
            self.update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.valid_response)

    def test_invalid_update(self):
        """
        Проверка при инвалидных данных.
        Должен вернуть HTTP_400_BAD_REQUEST
        """
        update_url = reverse('couriers-detail', args=[1])
        response = self.client.patch(
            update_url,
            self.invalid_update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
