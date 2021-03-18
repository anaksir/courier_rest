from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Courier, WorkingHour, Region
from .models import Item


class CourierSerializer(serializers.ModelSerializer):
    """
    Тестовый
    """
    # working_hours = serializers.SlugRelatedField(
    #     many=True,
    #     slug_field='interval',
    #     queryset=WorkingHour.objects.all()
    # )

    regions = serializers.ListField(child=serializers.IntegerField())

    class Meta:
        model = Courier
        fields = ('courier_id', 'courier_type', 'regions')

    #
    # def to_internal_value(self, data):
    #     print(data)
    #     return 'OK'


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
        except ValidationError:
            raise ValidationError({'id': data['courier_id']})

        return ret

    # def create(self, validated_data):
    #     regions_data = validated_data.pop('regions')
    #     workhours_data = validated_data.pop('working_hours')
    #     new_courier = Courier.objects.create(**validated_data)
    #     return new_courier



# class CourierData:
#     def __init__(self, data):
#         self.data = data


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
            couriers.append(new_courier)
        return {'couriers': couriers}

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     couriers = data.pop('data')
    #     data['couriers'] = couriers
    #     return data


class ItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ('item_name', 'item_price', 'id')
        extra_kwargs = {
            'id': {'read_only': True},
            'item_name': {'write_only': True},
            'item_price': {'write_only': True},
        }


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
