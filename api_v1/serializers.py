from rest_framework import serializers
# from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework.utils.serializer_helpers import ReturnDict
from .models import Courier, TimeInterval, Region
from .models import Item
from django.core.exceptions import ObjectDoesNotExist
from drf_writable_nested.serializers import WritableNestedModelSerializer


class CourierCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания курьера.
    Использует разные названия полей для серализаии и десериализации
    """
    working_hours = serializers.ListField(
        child=serializers.CharField(max_length=11),
        write_only=True,
        help_text="List of courier's working hours"
    )
    regions = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        write_only=True,
        help_text="List of courier's working regions"
    )

    id = serializers.IntegerField(
        min_value=1,
        source='courier_id',
        read_only=True,
    )

    class Meta:
        model = Courier
        fields = ('courier_id', 'courier_type', 'working_hours', 'regions', 'id')
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

    def to_internal_value(self, data):
        """
        Переопределяем метод, чтобы в слуае возникновения любых ошибок
        валидации вернуть id записей, не прошедших проверку.
        """
        try:
            ret = super().to_internal_value(data)
        except serializers.ValidationError as exc:
            print(exc.detail)
            print(data['courier_id'])
            raise serializers.ValidationError(data['courier_id'])

        return ret

    # def create(self, validated_data):
    #     regions_data = validated_data.pop('regions')
    #     workhours_data = validated_data.pop('working_hours')
    #     new_courier = Courier.objects.create(**validated_data)
    #     return new_courier


class CourierUpdateSerializer(serializers.ModelSerializer):

    working_hours = serializers.StringRelatedField(many=True, read_only=False)
    regions = serializers.ListField(write_only=True)

    class Meta:
        model = Courier
        fields = ('courier_id', 'courier_type', 'working_hours', 'regions')
        extra_kwargs = {
            'courier_id': {'read_only': True},
            'regions': {'validators': []},
        }

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError(
                f'Unknown field(s): {", ".join(unknown)}'
            )
        return attrs


class CustomRegionsRelatedField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        queryset = self.get_queryset()
        try:
            ret, _ = queryset.get_or_create(pk=data)
            return ret
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class NewTestCourierUpdateSerializer(serializers.ModelSerializer):
    regions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Region.objects.all()
    )
    working_hours = serializers.SlugRelatedField(
        many=True,
        slug_field='interval',
        queryset=TimeInterval.objects.all()
    )

    class Meta:
        model = Courier
        fields = ('courier_id', 'courier_type', 'working_hours', 'regions')
        extra_kwargs = {
            'courier_id': {'read_only': True},
        }

    def update(self, instance, validated_data):
        return instance


class TestCustomRelatedCourierUpdateSerializer(serializers.ModelSerializer):
    regions = CustomRegionsRelatedField(
        many=True,
        queryset=Region.objects.all()
    )

    class Meta:
        model = Courier
        fields = ('courier_id', 'courier_type', 'working_hours', 'regions')
        extra_kwargs = {
            'courier_id': {'read_only': True},
        }


class CourierDataSerializer(serializers.Serializer):
    """
    Сериализатор для с приема вложенного json с ключем 'data',
    в котором содержится спискок параметров курьеров
    """
    data = CourierCreateSerializer(many=True, write_only=True)
    couriers = CourierCreateSerializer(many=True, read_only=True)

    class Meta:
        fields = ('data', 'couriers')

    def create(self, validated_data):
        couriers = []
        for courier_data in validated_data['data']:
            regions_data = courier_data.pop('regions')
            workhours_data = courier_data.pop('working_hours')
            new_courier = Courier.objects.create(**courier_data)
            regions = (
                Region.objects.get_or_create(region_id=region)[0]
                for region in regions_data
            )
            new_courier.regions.add(*regions)

            work_hours = []
            for interval in workhours_data:
                start, end = interval.split('-')
                new_working_hour, _ = TimeInterval.objects.get_or_create(
                    start=start,
                    end=end,
                )
                work_hours.append(new_working_hour)
            new_courier.working_hours.add(*work_hours)

            couriers.append(new_courier)
        return {'couriers': couriers}

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     couriers = data.pop('data')
    #     data['couriers'] = couriers
    #     return data


class ItemCreateSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(
        min_value=1,
        write_only=True,
        source='id',
    )

    item_name = serializers.CharField(
        source='name',
        write_only=True,
    )

    item_quantity = serializers.IntegerField(
        required=True,
        min_value=1,
        write_only=True,
        source='quantity'
    )

    class Meta:
        model = Item
        fields = ('item_id', 'item_name', 'item_quantity', 'id')
        extra_kwargs = {
            'id': {'read_only': True},
        }

    def to_internal_value(self, data):
        try:
            ret = super().to_internal_value(data)
        except serializers.ValidationError as exc:
            print(exc)
            raise serializers.ValidationError({'id': data['item_id']})

        return ret


class ItemDataSerializer(serializers.Serializer):
    items_data = ItemCreateSerializer(many=True)

    class Meta:
        fields = ('items_data',)

    def create(self, validated_data):
        items = validated_data.pop('items_data')
        # for item_data in items:
        #     Item.objects.create(**item_data)
        created_items = (Item.objects.create(**item_data) for item_data in items)
        return {'items_data': created_items}
