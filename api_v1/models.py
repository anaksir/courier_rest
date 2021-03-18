from django.db import models


class Region(models.Model):
    region_id = models.PositiveSmallIntegerField(primary_key=True)

    def __str__(self):
        return f'{self.region_id}'


class WorkingHour(models.Model):
    interval = models.CharField(max_length=11)

    def __str__(self):
        return self.region_id


class Courier(models.Model):

    class Transport(models.TextChoices):
        FOOT = 'foot'
        BIKE = 'bike'
        CAR = 'car'

    id = models.PositiveIntegerField(primary_key=True,)
    courier_type = models.CharField(
        max_length=4,
        choices=Transport.choices,
    )

    regions = models.ManyToManyField(Region)
    working_hours = models.ManyToManyField(WorkingHour)


class Item(models.Model):

    item_price = models.PositiveIntegerField()
    item_name = models.CharField(max_length=100)
