from rest_framework import serializers

from .services.planner import departure_window

INTERVAL_CHOICES = (10, 25, 50)


class DepartureField(serializers.DateTimeField):
    def to_internal_value(self, value):
        departure = super().to_internal_value(value)
        earliest, latest = departure_window()
        if not earliest <= departure <= latest:
            raise serializers.ValidationError("Departure must be between now and 7 days ahead.")
        return departure


class PlanRequestSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=200)
    destination = serializers.CharField(max_length=200)
    departure = DepartureField()
    load_weight_lb = serializers.IntegerField(min_value=1, max_value=200_000)
    interval_miles = serializers.ChoiceField(choices=INTERVAL_CHOICES)


class HeatmapRequestSerializer(serializers.Serializer):
    corridor = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2),
        min_length=2,
        max_length=3000,
    )
    departure = DepartureField()
    load_weight_lb = serializers.IntegerField(min_value=1, max_value=200_000)
    hours = serializers.IntegerField(min_value=1, max_value=48, default=48)

    def validate_corridor(self, value):
        for lat, lon in value:
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise serializers.ValidationError("Invalid coordinate in corridor.")
        return [(lat, lon) for lat, lon in value]
