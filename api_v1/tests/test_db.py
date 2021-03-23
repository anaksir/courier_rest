from django.test import TestCase
from ..models import Region, Courier, WorkingHour


class CreateTest(TestCase):

    def test_create(self):

        input_data = {"data":
            [
                {
                    "courier_id": 1,
                    "courier_type": "foot",
                    "regions": [1, 12, 13],
                    "working_hours": ["11:35-14:05", "09:00-11:00"]
                },
                {
                    "courier_id": 2,
                    "courier_type": "car",
                    "regions": [22],
                    "working_hours": ["09:00-18:00"]
                },
                {
                    "courier_id": 3,
                    "courier_type": "foot",
                    "regions": [12, 22, 23, 33],
                    "working_hours": []
                }
            ]
        }

        couriers = []
        for courier_data in input_data['data']:
            regions_data = courier_data.pop('regions')
            workhours_data = courier_data.pop('working_hours')
            new_courier = Courier.objects.create(**courier_data)
            regions = [Region.objects.get_or_create(region_id=region)[0]
                       for region in regions_data
                       ]
            print(regions)
            new_courier.regions.add(*regions_data)

            work_hours = []
            for interval in workhours_data:
                start, end = interval.split('-')
                new_working_hour, _ = WorkingHour.objects.get_or_create(
                    start=start,
                    end=end,
                )
                work_hours.append(new_working_hour)

            print(work_hours)
            new_courier.working_hours.add(*work_hours)

            couriers.append(new_courier)

        print(couriers)
