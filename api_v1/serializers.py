import operator
from datetime import datetime
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Sum
from django.utils import timezone
from functools import reduce
from .models import Courier, TimeInterval, Region, Order, AssignedOrder


class RegionRelatedField(serializers.PrimaryKeyRelatedField):
    """
    Кастомное поле на основе PrimaryKeyRelatedField,
    создает Region, если его еще не было в базе
    """
    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            return queryset.get(pk=data)
        except ObjectDoesNotExist:
            return queryset.create(pk=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class TimeIntervalRelatedField(serializers.SlugRelatedField):
    """
    Кастомное поле на основе SlugRelatedField,
    создает TimeInterval, если его еще не было в базе
    """
    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            start, end = data.split('-')
            datetime.strptime(start, '%H:%M')
            datetime.strptime(end, '%H:%M')
            return queryset.get(**{self.slug_field: data})
        except ObjectDoesNotExist:
            return queryset.create(**{self.slug_field: data})
        except (TypeError, ValueError):
            self.fail('invalid')


class CourierCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор используется как вложенный при создании курьеров.
    Возвращает id созданного курьера.
    """
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
                'help_text':
                    'Transport for the courier, may be either foot, bike or car'
            },
            'courier_id': {
                'write_only': True,
                'min_value': 1,
                'help_text': 'Unique ID for courier, must be integer > 0',
            },
        }


class CourierDataSerializer(serializers.Serializer):
    """
    Сериализатор для создания курьеров,
    Данные о курьерах находятся в списке по ключу "data"
    Возвращает список созданных курьеров в ключе "couriers"
    """
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
    """
    Сериализатор для обновления курьеров.
    Возвращает актуальные данные.
    В методе 'update' реализовано снятие с курьера заказов, которые ему
    больше не подходят.
    """
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

    def validate(self, attrs):
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields or 'courier_id' in self.initial_data:
            raise ValidationError(
                f'Unknown field(s): {", ".join(unknown_fields)}'
            )
        return attrs

    def update(self, instance, validated_data):
        super().update(instance, validated_data)
        courier_working_hours = instance.working_hours.all()
        # Проходим по всем интервалам работы курьера и формируем условия:
        time_conditions = []
        for interval in courier_working_hours:
            time_conditions.append(
                Q(
                    Q(order__delivery_hours__start__lt=interval.end) &
                    Q(order__delivery_hours__end__gt=interval.start)
                )
            )
        # Отфильтровываем заказы, не подходящие по новым параметрам:
        unsuitable_orders = instance.assigned_orders.exclude(
            Q(order__weight__lte=instance.max_weights[instance.courier_type]),
            Q(order__region__in=instance.regions.all()),
            reduce(operator.or_, time_conditions)
        )
        # Сбрасываем назначение у ранее назначенных заказов:
        Order.objects.filter(assignedorder__in=unsuitable_orders).update(
            is_assigned=False
        )
        # Удаляем неподходящие заказы из таблицы назначенных заказов:
        unsuitable_orders.delete()
        return instance


class CourierInfoSerializer(CourierUpdateSerializer):
    """
    Сериализатор, возвращающий информацию о курьере.
    Вычисляет два поля, rating и earnings
    """
    rating = serializers.SerializerMethodField()
    earnings = serializers.SerializerMethodField()

    def get_rating(self, courier):
        t = 800
        rating = (60 * 60 - min(t, 60 * 60)) / (60 * 60) * 5
        return round(rating, 2)

    def get_earnings(self, courier):
        earning_data = (
            courier.assigned_orders.filter(is_competed=True)
            .aggregate(earning=Sum('payment'))
        )
        print(earning_data)
        return earning_data['earning'] or 0

    class Meta:
        model = Courier
        fields = (
            'courier_id',
            'courier_type',
            'regions',
            'working_hours',
            'rating',
            'earnings'
        )



class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания заказа, используется как вложенный в
    OrderDataSerializer
    """
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
    """
    Сериализатор для создания заказов,
    Данные о заказах находятся в списке по ключу "data"
    Возвращает список созданных заказов в ключе "orders"
    """
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


class CompleteOrderSerializer(serializers.Serializer):
    """
    Сериализатор для выполненных заказов
    """
    courier_id = serializers.IntegerField(write_only=True)
    order_id = serializers.IntegerField()
    complete_time = serializers.DateTimeField(write_only=True)

    class Meta:
        fields = ('courier_id', 'order_id', 'complete_time')

    def validate(self, attrs):
        if not AssignedOrder.objects.filter(
            courier_id=attrs['courier_id'],
            order_id=attrs['order_id'],
            is_competed=False
        ).exists():
            raise serializers.ValidationError(
                detail='Assigned order not found'
            )

        return attrs

    @staticmethod
    def calculate_payment(courier_id):
        courier_type_coeffs = {
            'foot': 2,
            'bike': 5,
            'car': 9
        }
        base_payment = 500
        courier = Courier.objects.get(courier_id=courier_id)
        payment = courier_type_coeffs.get(courier.courier_type) * base_payment
        return payment

    def create(self, validated_data):
        courier_id = validated_data['courier_id']
        order_id = validated_data['order_id']
        complete_time = validated_data['complete_time']
        completed_order = AssignedOrder.objects.filter(order_id=order_id)
        payment = self.calculate_payment(courier_id)
        completed_order.update(
            is_competed=True,
            complete_time=complete_time,
            payment=payment
        )
        return {'order_id': order_id}


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
        model = AssignedOrder
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
            Q(weight__lte=courier.max_weights[courier.courier_type]),
            reduce(operator.or_, time_conditions)
        )
        assigned_orders = []
        assign_time = timezone.now()
        # В цикле проходим по подходящим заказам,
        # создаем новый объект OrderAssign
        for order in suitable_orders:
            new_assigned_order = AssignedOrder.objects.create(
                courier=courier,
                order=order,
                assign_time=assign_time

            )
            assigned_orders.append(new_assigned_order)
        # Для назначенных заказов записываем признак 'is_assigned=True',
        # чтобы они не были назначены другому курьеру
        suitable_orders.update(is_assigned=True)
        # Фильтруем назначенные на курьера, но не выполненные заказы,
        # для использования в ответе:
        assigned_to_courier = courier.assigned_orders.filter(
            is_competed=False
        )
        result = {'orders': assigned_orders}
        # Если заказы назначены, в ответ добавить время назначения
        if assigned_orders:
            result.update(assign_time=assign_time)
        return result
