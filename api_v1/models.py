from django.db import models
import datetime


class Region(models.Model):
    region_id = models.PositiveIntegerField(primary_key=True)

    def __str__(self):
        return f'{self.region_id}'


class TimeInterval(models.Model):
    interval = models.CharField(max_length=11, unique=True)
    start = models.TimeField()
    end = models.TimeField()

    @property
    def get_time(self):
        return self.interval.split('-')

    def save(self, *args, **kwargs):
        self.start, self.end = self.get_time
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.start}-{self.end}'


class Courier(models.Model):

    class Transport(models.TextChoices):
        FOOT = 'foot'
        BIKE = 'bike'
        CAR = 'car'

    courier_id = models.PositiveIntegerField(primary_key=True)
    courier_type = models.CharField(
        max_length=4,
        choices=Transport.choices,
    )

    regions = models.ManyToManyField(Region)
    working_hours = models.ManyToManyField(TimeInterval)


class Order(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    weight = models.DecimalField(max_digits=4, decimal_places=2)
    region = models.ForeignKey(
        Region,
        related_name='orders',
        on_delete=models.CASCADE,
    )
    delivery_hours = models.ManyToManyField(TimeInterval)


class Item(models.Model):

    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
