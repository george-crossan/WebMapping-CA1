from rest_framework import generics
from .serializers import EventSerializer, EventListSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.http import JsonResponse
from .models import Event
from django.db import models
import json, traceback
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance


class EventListCreateView(generics.ListCreateAPIView):
    queryset = Event.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EventListSerializer
        return EventSerializer

class EventDetailView(generics.ListAPIView):
    queryset = Event.objects.all().order_by('-start_date')
    serializer_class = EventSerializer


@api_view(['GET'])
def events_geojson(request):
    """Return events data in GeoJSON format for Leaflet"""
    events = Event.objects.all()

    features = []
    for event_data in events:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(event_data.longitude), float(event_data.latitude)]
            },
            "properties": {
                "id": event_data.id,
                "name": event_data.name,
                "venue": event_data.venue,
                "city": event_data.city,
                "country": event_data.country,
                "start_date": event_data.start_date.isoformat(),
                "url": event_data.url,
            }
        })

    return JsonResponse({
        "type": "FeatureCollection",
        "features": features
    }, safe=False)

def map_view(request):
    """Render the main map page"""
    return render(request, 'events/map.html')

def map_search_view(request):
    return render(request, 'search/map.html')

def event_list(request):
    """Display list of all spatial cities"""

    events = Event.objects.all().order_by("name")
    print(events)

    return render(request, "search/event_list.html", {"events": events})

@api_view(['GET'])
def event_search(request):
    """Search events by name or city"""
    query = request.GET.get('q', '')
    if query:
        events = Event.objects.filter(
            models.Q(name__icontains=query) |
            models.Q(city_iconations=query)
        )
    else:
        events = Event.objects.all()
   
    serializer = EventListSerializer(events, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def find_nearest_events(request):
    """
    Find the 10 nearest events to a given point
    POST /api/events/nearest/
    Body: {"lat": 53.3498, "lng": -6.2603}
    """
    try:
        print("DEBUG: Method =", request.method)
        print("DEBUG: Raw body =", request.body)

        data = json.loads(request.body.decode('utf-8'))
        print("DEBUG: Parsed data =", data)

        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        data = request.data
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))

        print("line 103")
        # Validate coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return Response({
                'error': 'Invalid coordinates. Lat must be -90 to 90, lng must be -180 to 180'
            }, status=400)
        
        # Create a point from coordinates (PostGIS uses lng, lat order)
        search_point = Point(lng, lat, srid=4326)

        # Query for nearest 10 events using PostGIS distance calculation
        nearest_events = Event.objects.annotate(
            distance=Distance('location', search_point)
        ).order_by('distance')[:10]

        # Serialize results
        results = []
        for i, event in enumerate(nearest_events, 1):
            results.append({
                'rank': i,
                'id': event.id,
                'name': event.name,
                'country': event.country,
                'city': event.city,
                'coordinates': {
                    'lat': event.latitude,
                    'lng': event.longitude
                },
                'distance_km': round(event.distance.km, 2),
                'distance_miles': round(event.distance.mi, 2),
                'venue': event.venue,
                'start_date': event.start_date,
                'url': event.url,
            })
        return Response({
            'search_point': {'lat': lat, 'lng': lng},
            'total_found': len(results),
            'nearest_events': results
        })
    
    except (ValueError, TypeError) as e:
        return Response({
            'error': f'Invalid input: {str(e)}'
        }, status=400)
    
    except Exception as e:
        traceback.print_exc()
        return Response({
            'error': f'Server error: {str(e)}'
        }, status=500)


@api_view(['POST'])
def events_within_radius(request):
    """
    Find all events within a specified radius
    POST /api/events/radius
    Body: {"lat": 53.3498, "lng": -6.2603, "radius_km": 100}
    """

    try:
        data = request.data
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        radius_km = float(data.get('radius_km', 100))  # Default 100km
       
        # Validate inputs
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return Response({'error': 'Invalid coordinates'}, status=400)
       
        if radius_km <= 0 or radius_km > 20000:  # Max ~half Earth circumference
            return Response({'error': 'Radius must be between 0 and 20000 km'}, status=400)
       
        search_point = Point(lng, lat, srid=4326)
        
        # Use PostGIS distance filter
        from django.contrib.gis.measure import Distance as D
        events_in_radius = Event.objects.filter(
            location__distance_lte=(search_point, D(km=radius_km))
        ).annotate(
            distance=Distance('location', search_point)
        ).order_by('distance')
       
        results = []
        for event in events_in_radius:
            results.append({
                'id': event.id,
                'name': event.name,
                'country': event.country,
                'city': event.city,
                'coordinates': {
                    'lat': event.latitude,
                    'lng': event.longitude
                },
                'distance_km': round(event.distance.km, 2),
                'distance_miles': round(event.distance.mi, 2),
                'venue': event.venue,
                'start_date': event.start_date,
                'url': event.url,
            })
        
        return Response({
            'search_point': {'lat': lat, 'lng': lng},
            'radius_km': radius_km,
            'total_found': len(results),
            'events': results
        })
    
    except (ValueError, TypeError) as e:
        return Response({
            'error': f'Invalid input: {str(e)}'
        }, status=400)
    
    except Exception as e:
        return Response({
            'error': f'Server error: {str(e)}'
        }, status=500)
