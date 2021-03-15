from rest_framework import serializers
from .models import Courier, WorkingHour


class WorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHour
        fields = ('interval',)


class CourierSerializer(serializers.ModelSerializer):
    working_hours = serializers.StringRelatedField(many=True)

    class Meta:
        model = Courier
        fields = '__all__'


class CourierDataSerializer(serializers.Serializer):
    data = CourierSerializer(many=True)

    class Meta:
        fields = ('data',)

    def create(self, validated_data):
        pass


