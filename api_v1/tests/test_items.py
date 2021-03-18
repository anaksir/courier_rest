from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import Item


class ItemsTests(APITestCase):
    def test_create_items(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('items-list')
        data = {
            "items_data": [
                        {
                            "item_name": "Foo",
                            "item_price": 1000
                        },
                        {
                            "item_name": "Bar",
                            "item_price": 99
                        }
                    ]
        }

        response_data = {"couriers": [{"id": 1}, {"id": 2}, {"id": 3}]}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print('response.data')
        print(response.data)
        self.assertEqual(Item.objects.count(), 2)
        # self.assertEqual(response.data, response_data)
        print('test_create_couriers OK')