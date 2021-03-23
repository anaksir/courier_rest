from rest_framework import serializers
# from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework.utils.serializer_helpers import ReturnDict
from .models import Courier, TimeInterval, Region
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


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ('region_id',)


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
