from django.db import models


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
    max_weights = {
        'foot': 10,
        'bike': 15,
        'car': 50
    }

    class Transport(models.TextChoices):
        FOOT = 'foot', '10'
        BIKE = 'bike', '15'
        CAR = 'car', '50'

    courier_id = models.PositiveIntegerField(primary_key=True)
    courier_type = models.CharField(
        max_length=4,
        choices=Transport.choices
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
    is_assigned = models.BooleanField(default=False)


class AssignedOrder(models.Model):
    courier = models.ForeignKey(
        Courier,
        on_delete=models.CASCADE,
        related_name='assigned_orders'
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        primary_key=True
    )
    assign_time = models.DateTimeField()
    complete_time = models.DateTimeField(null=True, blank=True)
    delivery_time = models.DurationField(null=True, blank=True)
    is_competed = models.BooleanField(default=False)
    payment = models.IntegerField(null=True, blank=True)

