from rest_framework import serializers
# from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework.utils.serializer_helpers import ReturnDict
from .models import Courier, TimeInterval, Region, Order
from django.core.exceptions import ObjectDoesNotExist
from drf_writable_nested.serializers import WritableNestedModelSerializer


class RegionRelatedField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            return queryset.get(pk=data)
        except ObjectDoesNotExist:
            return queryset.create(pk=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class TimeIntervalRelatedField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            return queryset.get(**{self.slug_field: data})
        except ObjectDoesNotExist:
            return queryset.create(**{self.slug_field: data})
        except (TypeError, ValueError):
            self.fail('invalid')


class CourierCreateSerializer(serializers.ModelSerializer):
    regions = RegionRelatedField(
        many=True,
        queryset=Region.objects.all(),
        write_only=True,
    )

    working_hours = TimeIntervalRelatedField(
        many=True,
        slug_field='interval',
        queryset=TimeInterval.objects.all(),
        write_only=True,
    )

    id = serializers.IntegerField(
        source='courier_id',
        read_only=True,
    )

    class Meta:
        model = Courier
        fields = (
            'courier_id',
            'courier_type',
            'working_hours',
            'regions',
            'id',
        )

        extra_kwargs = {
            'courier_type': {
                'write_only': True,
                'help_text': 'Transport for the courier, may be either foot, bike or car'
            },
            'courier_id': {
                'write_only': True,
                'min_value': 1,
                'help_text': 'Unique ID for courier, must be integer > 0',
            },
        }


class CourierDataSerializer(serializers.Serializer):
    data = CourierCreateSerializer(many=True, write_only=True)
    couriers = CourierCreateSerializer(many=True, read_only=True)

    class Meta:
        fields = ('data', 'couriers')

    def create(self, validated_data):
        couriers = []
        for courier_data in validated_data['data']:
            courier_regions = courier_data.pop('regions')
            courier_hours = courier_data.pop('working_hours')
            new_courier = Courier.objects.create(**courier_data)
            new_courier.regions.add(*courier_regions)
            new_courier.working_hours.add(*courier_hours)
            couriers.append(new_courier)

        return {'couriers': couriers}


class CourierUpdateSerializer(serializers.ModelSerializer):
    regions = RegionRelatedField(
        many=True,
        queryset=Region.objects.all(),
    )

    working_hours = TimeIntervalRelatedField(
        many=True,
        slug_field='interval',
        queryset=TimeInterval.objects.all(),
    )

    class Meta:
        model = Courier
        fields = (
            'courier_id',
            'courier_type',
            'working_hours',
            'regions',
        )

        extra_kwargs = {
            'courier_id': {
                'read_only': True,
            },
        }


class OrderCreateSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(
        min_value=1,
        validators=[UniqueValidator(queryset=Order.objects.all())],
        write_only=True,
        source='id'
    )

    region = RegionRelatedField(
        queryset=Region.objects.all(),
        write_only=True
    )

    delivery_hours = TimeIntervalRelatedField(
        many=True,
        slug_field='interval',
        queryset=TimeInterval.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Order
        fields = (
            'order_id',
            'weight',
            'region',
            'delivery_hours',
            'id',
        )

        extra_kwargs = {
            'weight': {
                'write_only': True,
                'min_value': 0.009,
                'max_value': 50,
            },
            'id': {
                'read_only': True,
            },
        }


class OrderDataSerializer(serializers.Serializer):
    data = OrderCreateSerializer(many=True, write_only=True)
    orders = OrderCreateSerializer(many=True, read_only=True)

    def create(self, validated_data):
        print('-'*80)
        print(validated_data)
        orders = []
        for order_data in validated_data['data']:
            delivery_hours = order_data.pop('delivery_hours')
            new_order = Order.objects.create(**order_data)
            new_order.delivery_hours.add(*delivery_hours)
            orders.append(new_order)

        return {'orders': orders}


class OrderAssignSerializer(serializers.Serializer):
    courier_id = serializers.PrimaryKeyRelatedField(
        queryset=Courier.objects.all(),
        write_only=True,
    )
    orders = OrderCreateSerializer(
        many=True,
        read_only=True
    )
    assign_time = serializers.DateTimeField()