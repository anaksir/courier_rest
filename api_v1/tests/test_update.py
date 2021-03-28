from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response
from ..models import Courier, Order


class CouriersTests(APITestCase):
    """
    Проверка обновления информации о курьере.
    """
    def test_update_couriers(self):
        """
        Проверка создания валидных курьеров.
        """
        create_url = reverse('couriers-list')
        courier_data = {
            "data": [
                {
                    "courier_id": 1,
                    "courier_type": "foot",
                    "regions": [1, 12, 22],
                    "working_hours": ["11:35-14:05", "09:00-11:00"]
                }
             ]
        }
        self.client.post(create_url, courier_data, format='json')

        update_url = reverse('couriers-detail', args=[1])
        update_data = {
            "courier_type": "car",
            "regions": [13],
        }

        response = self.client.patch(update_url, update_data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        valid_response = {
            'courier_id': 1,
            'courier_type': 'car',
            'working_hours': ['11:35-14:05', '09:00-11:00'],
            'regions': [13]
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, Response(valid_response).data)
