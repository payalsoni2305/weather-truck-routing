import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import HeatmapRequestSerializer, PlanRequestSerializer
from .services.geocoding import GeocodingError
from .services.heatmap import build_heatmap
from .services.planner import TripRequest, plan_trip
from .services.routing import RoutingError
from .services.weather import WeatherError

logger = logging.getLogger(__name__)


def _upstream_error(exc):
    logger.warning("Upstream service error: %s", exc)
    return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class PlanView(APIView):
    def post(self, request):
        serializer = PlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = plan_trip(TripRequest(**serializer.validated_data))
        except GeocodingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except (RoutingError, WeatherError) as exc:
            return _upstream_error(exc)
        return Response(result)


class HeatmapView(APIView):
    def post(self, request):
        serializer = HeatmapRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            result = build_heatmap(
                data["corridor"], data["departure"].timestamp(), data["hours"], data["load_weight_lb"]
            )
        except WeatherError as exc:
            return _upstream_error(exc)
        return Response(result)


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok"})
