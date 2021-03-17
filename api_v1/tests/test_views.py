from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import Courier


class CouriersTests(APITestCase):
    def test_create_couriers(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('couriers-list')
        data = {
            "data": [
                {
                    "courier_id": 1,
                    "courier_type": "foot",
                    "regions": [1, 12, 22],
                    "working_hours": ["11:35-14:05", "09:00-11:00"]
                },
                {
                    "courier_id": 2,
                    "courier_type": "bike",
                    "regions": [22],
                    "working_hours": ["09:00-18:00"]
                },
                {
                    "courier_id": 3,
                    "courier_type": "car",
                    "regions": [12, 22, 23, 33],
                    "working_hours": []
                }
            ]
        }

        response_data = {"couriers": [{"id": 1}, {"id": 2}, {"id": 3}]}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Courier.objects.count(), 3)
        self.assertEqual(response.data, response_data)
        print('test_create_couriers OK')

    def test_create_invalid_couriers(self):
        """
        Проверка ответа при невалидных данных
        """
        url = reverse('couriers-list')
        data = {
            "data": [
                {
                    "courier_id": 1,
                    "courier_type": "blablabla",
                    "regions": [1, 12, 22],
                    "working_hours": ["11:35-14:05", "09:00-11:00"]
                },
                {
                    "courier_id": 2,
                    "courier_type": "bike",
                    "regions": [22],
                    "working_hours": ["09:00-18:00"]
                },
                {
                    "courier_id": 'foo',
                    "courier_type": "car",
                    "regions": [12, 22, 23, 33],
                    "working_hours": []
                }
            ]
        }

        response_data = {
            "validation_error": {
                "couriers": [
                    {"id": 1},
                    {"id": 2},
                ]
            }
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, response_data)
