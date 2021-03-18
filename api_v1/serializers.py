from rest_framework import serializers
from .models import Courier, WorkingHour, Region
from .models import Item


class CourierSerializer(serializers.ModelSerializer):
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
    working_hours = serializers.ListField(
        child=serializers.CharField(max_length=11),
        write_only=True
    )
    regions = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        write_only=True
    )

    id = serializers.IntegerField(source='courier_id', read_only=True)

    class Meta:
        model = Courier
        fields = ('courier_id', 'courier_type', 'working_hours', 'regions', 'id')
        extra_kwargs = {
            'courier_type': {'write_only': True},
            'courier_id': {'write_only': True},
        }

    def create(self, validated_data):
        regions_data = validated_data.pop('regions')
        workhours_data = validated_data.pop('working_hours')
        new_courier = Courier.objects.create(**validated_data)
        return new_courier


class CourierData:
    def __init__(self, data):
        self.data = data


class CourierDataSerializer(serializers.Serializer):
    data = CourierCreateSerializer(many=True)

    class Meta:
        fields = ('data',)

    def create(self, validated_data):
        serializer = CourierCreateSerializer(
            data=validated_data['data'],
            many=True,
        )
        if serializer.is_valid(raise_exception=True):
            couriers = serializer.save()
        return CourierData(**validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        couriers = data.pop('data')
        data['couriers'] = couriers
        return data


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
