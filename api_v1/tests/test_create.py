from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.response import Response
from ..models import Courier, Order


class CouriersTests(APITestCase):
    """
    Проверка создания курьеров POST /couriers.
    """
    def test_create_couriers(self):
        """
        Проверка создания валидных курьеров.
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
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            'Проверка статуса ответа HTTP_201_CREATED'
        )
        self.assertEqual(
            Courier.objects.count(),
            3,
            'Проверка, что создано 3 курера'
        )
        self.assertEqual(
            response.data,
            response_data,
            'Проверка данных ответа'
        )

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

        response_data = {
            "validation_error": {
                "couriers": [{"id": 1}, {"id": 3}, {"id": 4}]
            }
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, Response(response_data).data)


class OrderTests(APITestCase):
    """
    Проверка создания курьеров POST /couriers.
    """
    def test_create_couriers(self):
        """
        Проверка создания валидных заказов.
        """
        url = reverse('orders-list')
        data = {
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

        response_data = {"orders": [{"id": 1}, {"id": 2}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            'Проверка статуса ответа HTTP_201_CREATED'
        )
        self.assertEqual(
            Order.objects.count(),
            2,
            'Проверка, что создано 2 заказа'
        )
        self.assertEqual(
            response.data,
            response_data,
            'Проверка данных ответа'
        )

    def test_create_invalid_couriers(self):
        """
        Проверка ответа при невалидных данных
        """
        url = reverse('orders-list')
        data = {
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

        response_data = {
            "validation_error": {
                "orders": [{"id": 1}, {"id": 2}]
            }
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, Response(response_data).data)