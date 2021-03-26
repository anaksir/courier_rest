from rest_framework import serializers
# from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework.utils.serializer_helpers import ReturnDict
from .models import Courier, TimeInterval, Region, Order, OrderAssign
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from drf_writable_nested.serializers import WritableNestedModelSerializer
import datetime
from functools import reduce
import operator
from django.utils import timezone


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
        orders = []
        for order_data in validated_data['data']:
            delivery_hours = order_data.pop('delivery_hours')
            new_order = Order.objects.create(**order_data)
            new_order.delivery_hours.add(*delivery_hours)
            orders.append(new_order)

        return {'orders': orders}


class AssignedOrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для назначенных заказов,
    используется в OrderAssignSerializer
    """
    id = serializers.IntegerField(
        source='order_id',
        read_only=True
    )

    class Meta:
        model = OrderAssign
        fields = ('id',)


class OrderAssignSerializer(serializers.Serializer):
    courier_id = serializers.PrimaryKeyRelatedField(
        queryset=Courier.objects.all(),
        write_only=True,
    )
    orders = AssignedOrderSerializer(
        many=True,
        read_only=True
    )
    assign_time = serializers.DateTimeField(
        read_only=True,
        required=False
    )

    class Meta:
        fields = (
            'courier_id',
            'orders',
            'assign_time',
        )

    def create(self, validated_data):
        """
        Назначает заказы курьеру
        """
        courier_max_weight = {
            'foot': 10,
            'bike': 15,
            'car': 50
        }

        courier = validated_data.pop('courier_id')
        courier_working_hours = courier.working_hours.all()

        # Вариант 2 как сделать фильтр по времени:
        # suitable_orders = Order.objects.none()
        # for interval in courier_working_hours:
        #     suitable_orders |= Order.objects.filter(
        #         Q(region__in=courier.regions.all()),
        #         Q(is_assigned=False),
        #         Q(weight__lte=courier_max_weight[courier.courier_type]),
        #         Q(delivery_hours__start__lt=interval.end) &
        #         Q(delivery_hours__end__gt=interval.start)
        #     )

        time_conditions = []
        # Проходим по всем интервалам работы курьера и формируем условия:
        for interval in courier_working_hours:
            time_conditions.append(
                Q(
                    Q(delivery_hours__start__lt=interval.end) &
                    Q(delivery_hours__end__gt=interval.start)
                )
            )
        # Затем по условиям фильтруем заказы
        suitable_orders = Order.objects.filter(
            Q(region__in=courier.regions.all()),
            Q(is_assigned=False),
            Q(weight__lte=courier_max_weight[courier.courier_type]),
            reduce(operator.or_, time_conditions)
        )
        assigned_orders = []
        assign_time = timezone.now()
        # В цикле проходим по подходящим заказам,
        # создаем новый объект OrderAssign
        for order in suitable_orders:
            new_assigned_order = OrderAssign.objects.create(
                courier=courier,
                order=order,
                assign_time=assign_time

            )
            assigned_orders.append(new_assigned_order)

        suitable_orders.update(is_assigned=True)
        result = {'orders': assigned_orders}
        # Если заказы назначены, в ответ добавить время назначения
        if assigned_orders:
            result.update(assign_time=assign_time)
        return result


