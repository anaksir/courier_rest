import operator
from datetime import datetime
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Sum, Avg, Min
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
            if start > end:
                self.fail('invalid')
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
        help_text='Working regions, array of integer, must be > 0 '
    )
    working_hours = TimeIntervalRelatedField(
        many=True,
        slug_field='interval',
        queryset=TimeInterval.objects.all(),
        write_only=True,
        help_text='Working hours, array of string with format: "HH:MM-HH:MM"'
    )
    id = serializers.IntegerField(
        source='courier_id',
        read_only=True,
        help_text='id of created courier'
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
                    'Transport for courier, may be either foot, bike or car'
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
        help_text='Working regions, array of integer, must be > 0 '
    )

    working_hours = TimeIntervalRelatedField(
        many=True,
        slug_field='interval',
        queryset=TimeInterval.objects.all(),
        help_text='Working hours, array of string with format: "HH:MM-HH:MM"'
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
        """
        Для проверки на наличие не прописанных полей
        """
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields or 'courier_id' in self.initial_data:
            raise ValidationError(
                f'Unknown field(s): {", ".join(unknown_fields)}'
            )
        return attrs

    def update(self, instance, validated_data):
        """
        Обновляет информацию о курьере, снимает заказы, которые больше не
        подходят
        """
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
    rating = serializers.SerializerMethodField(
        help_text='Rating of courier'
    )
    earnings = serializers.SerializerMethodField(
        help_text='Total payment'
    )

    def get_rating(self, courier):
        """
        Возвращает рейтинг курьера.
        Рейтинг рассчитывается следующим образом:
        (60*60 - min(t, 60*60))/(60*60) * 5
        где t - минимальное из средних времен доставки по районам (в секундах),
        t = min(td[1], td[2], ..., td[n])
        td[i]  - среднее время доставки заказов по району  i  (в секундах).
        Время доставки одного заказа определяется как разница между временем
        окончания этого заказа и временем окончания предыдущего заказа
        (или временем назначения заказов, если вычисляется время для первого
        заказа).
        """
        # Вычисляем минимальное среднее время доставки по регионам:
        t_min_delta = (courier.assigned_orders
                              .filter(is_competed=True)
                              .values('order_id__region')
                              .annotate(avg_time=Avg('delivery_time'))
                              .aggregate(t_min=Min('avg_time')))['t_min']
        # Если минимальная дельта не найдена, рейтинг не расчитываем
        if t_min_delta is None:
            return None
        t = t_min_delta.total_seconds()
        raw_rating = (60 * 60 - min(t, 60 * 60)) / (60 * 60) * 5
        return round(raw_rating, 2)

    def get_earnings(self, courier):
        earning_data = (
            courier.assigned_orders.filter(is_competed=True)
            .aggregate(earning=Sum('payment'))
        )
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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Не возвращать рейтинг, если он не расчитан
        if ret['rating'] is None:
            del ret['rating']
        return ret


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания заказа, используется как вложенный в
    OrderDataSerializer
    """
    order_id = serializers.IntegerField(
        min_value=1,
        validators=[UniqueValidator(queryset=Order.objects.all())],
        write_only=True,
        source='id',
        help_text='Unique ID for order, must be integer > 0'
    )
    region = RegionRelatedField(
        queryset=Region.objects.all(),
        write_only=True,
        help_text='Delivery region, must be integer > 0'
    )
    delivery_hours = TimeIntervalRelatedField(
        many=True,
        slug_field='interval',
        queryset=TimeInterval.objects.all(),
        write_only=True,
        help_text='Delivery time, array of string with format: "HH:MM-HH:MM"'
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
                'help_text': 'Weight of order, from 0.01 to 50'
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
    courier_id = serializers.IntegerField(
        write_only=True,
        help_text='ID of an existing courier'
    )
    order_id = serializers.IntegerField(
        help_text='ID of an existing order, assigned to courier'
    )
    complete_time = serializers.DateTimeField(
        write_only=True,
        help_text='Order completion time, format ISO 8601'
    )

    class Meta:
        fields = ('courier_id', 'order_id', 'complete_time')

    def validate(self, attrs):

        assigned_order = AssignedOrder.objects.filter(
            courier_id=attrs['courier_id'],
            order_id=attrs['order_id'],
            is_competed=False
        )
        if not assigned_order.exists():
            raise serializers.ValidationError(
                detail='Assigned order not found'
            )

        if not attrs['complete_time'] > assigned_order.first().assign_time:
            raise serializers.ValidationError(
                detail='complete_time must be greater than assign_time'
            )
        return attrs

    def create(self, validated_data):
        """
        Отмечает, что заказ выполнен, и записывает время выполнения и разницу
        между временем выполнения предыдущего заказа. Если заказы ранее не
        выполнялись, то разница берется от времни назанчения заказа.
        """
        courier_id = validated_data['courier_id']
        order_id = validated_data['order_id']
        complete_time = validated_data['complete_time']
        completed_order = AssignedOrder.objects.filter(order_id=order_id)
        # Находим предыдущий заказ
        previous_order = (
            AssignedOrder.objects
            .filter(courier_id=courier_id, is_competed=True)
            .order_by('-complete_time')
            .first()
        )
        if previous_order:
            previous_time = previous_order.complete_time
        else:
            # Если выполенных заказов ранее не было, то берем время назначения
            previous_time = completed_order.first().assign_time
        delivery_time = complete_time - previous_time
        completed_order.update(
            is_competed=True,
            complete_time=complete_time,
            delivery_time=delivery_time
        )

        return {'order_id': order_id}


class AssignedOrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для возврата назначенных заказов,
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
        help_text='ID of existing courier'
    )
    orders = AssignedOrderSerializer(
        many=True,
        read_only=True,
        help_text='Array on assigned orders, format {id: int}'
    )
    assign_time = serializers.DateTimeField(
        read_only=True,
        required=False,
        help_text='Time of assignment of orders '
    )

    class Meta:
        fields = (
            'courier_id',
            'orders',
            'assign_time',
        )

    @staticmethod
    def calculate_payment(courier_type):
        """
        Расчет суммы оплаты при завершении развоза.
        Оплата считается так: 500 * C
        C  — коэффициент, зависящий от типа курьера (пеший — 2, велокурьер — 5,
        авто — 9) на момент формирования развоза.
        """
        courier_type_coeffs = {
            'foot': 2,
            'bike': 5,
            'car': 9
        }
        base_payment = 500
        payment = courier_type_coeffs[courier_type] * base_payment
        return payment

    def create(self, validated_data):
        """
        Назначает заказы курьеру
        """
        courier = validated_data.pop('courier_id')
        courier_type = courier.courier_type
        courier_working_hours = courier.working_hours.all()

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
            Q(weight__lte=courier.max_weights[courier_type]),
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
                assign_time=assign_time,
                payment=self.calculate_payment(courier_type)
            )
            assigned_orders.append(new_assigned_order)
        # Для назначенных заказов записываем признак 'is_assigned=True',
        # чтобы они не были назначены другому курьеру
        if suitable_orders:
            suitable_orders.update(is_assigned=True)
        # Фильтруем назначенные на курьера, но не выполненные заказы,
        # для использования в ответе:
        # assigned_to_courier = courier.assigned_orders.filter(
        #     is_competed=False
        # )
        result = {'orders': assigned_orders}
        # Если заказы назначены, в ответ добавить время назначения
        if assigned_orders:
            result.update(assign_time=assign_time)
        return result
