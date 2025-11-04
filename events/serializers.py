from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    """Serializer for listing events"""
    latitude = serializers.ReadOnlyField()
    longitude = serializers.ReadOnlyField()

    class Meta:
        model = Event
        fields = [
            'id','name','venue','city','country',
            'start_date','url','latitude','longitude']

    def get_latitude(self, obj): return obj.location.y
    def get_longitude(self, obj): return obj.location.x

class EventListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    coordinates = serializers.ReadOnlyField()
   
    class Meta:
        model = Event
        fields = ['id', 'name', 'venue', 'city', 'country', 'coordinates']

class EventGeoJSONSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Event
        geo_field = 'location'
        fields = ['id','name','venue','city','country',
                  'start_date','url']
