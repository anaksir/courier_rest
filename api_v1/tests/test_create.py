from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import Courier, Order


class CouriersTests(APITestCase):
    """
    Проверка создания курьеров POST /couriers.
    """
    def setUp(self):
        self.valid_data = {
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
        self.valid_response = {"couriers": [{"id": 1}, {"id": 2}, {"id": 3}]}
        self.invalid_data = {
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
                    "courier_id": 3,
                    "courier_type": "bike",
                    "regions": [22],
                    "working_hours": ["sss:00-18:00"]
                },
                {
                    "courier_id": 4,
                    "courier_type": "car",
                    "regions": ["www", 22, 23, 33],
                    "working_hours": []
                }
            ]
        }
        self.invalid_response = {
            "validation_error": {"couriers": [{"id": 1}, {"id": 3}, {"id": 4}]}
        }

    def test_create_couriers(self):
        """
        Проверка создания валидных курьеров.
        """
        url = reverse('couriers-list')
        response = self.client.post(url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Courier.objects.count(), 3)
        self.assertEqual(response.data, self.valid_response)

    def test_create_invalid_couriers(self):
        """
        Проверка ответа при невалидных данных
        """
        url = reverse('couriers-list')
        response = self.client.post(url, self.invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, self.invalid_response)


class OrderTests(APITestCase):
    """
    Проверка создания заказов POST /orders.
    """
    def setUp(self):
        self.valid_data = {
            "data": [
                {
                    "order_id": 1,
                    "weight": 50,
                    "region": 13,
                    "delivery_hours": ["00:11-23:59"]
                },
                {
                    "order_id": 2,
                    "weight": 0.01,
                    "region": 1,
                    "delivery_hours": ["12:00-18:00"]
                }
            ]
        }
        self.valid_response = {"orders": [{"id": 1}, {"id": 2}]}
        self.invalid_data = {
            "data": [
                {
                    "order_id": 1,
                    "weight": 51,
                    "region": 13,
                    "delivery_hours": ["00:11-23:59"]
                },
                {
                    "order_id": 2,
                    "weight": 0.01,
                    "region": "sss",
                    "delivery_hours": ["12:00-18:00"]
                }
            ]
        }
        self.invalid_response = {
            "validation_error": {"orders": [{"id": 1}, {"id": 2}]}
        }

    def test_create_orders(self):
        """
        Проверка создания валидных заказов.
        """
        url = reverse('orders-list')
        response = self.client.post(url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(response.data, self.valid_response)

    def test_create_invalid_orders(self):
        """
        Проверка ответа при невалидных данных
        """
        url = reverse('orders-list')
        response = self.client.post(url, self.invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, self.invalid_response)
