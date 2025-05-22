from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import DentalClinic, ClinicImage
from .serializers import DentalClinicSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes
import math
import requests
from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from authentication.models import VisitedUserData


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_place_details(request):
    place_id = request.GET.get("place_id")

    if not place_id:
        return JsonResponse({"error": "Missing place_id"}, status=400)

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": settings.GOOGLE_MAPS_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    return JsonResponse(data)

class DentalClinicViewSet(viewsets.ModelViewSet):
    queryset = DentalClinic.objects.all()
    serializer_class = DentalClinicSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        # Allow unauthenticated access only to the 'nearby' action
        if self.action == 'nearby':
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    def get_serializer_context(self):
        """Add request to serializer context so it can access file data"""
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        print('request structure in views.py ==== ', request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Find clinics within a given radius (default: 10km) of the provided coordinates.
        
        Query parameters:
        - lat: user's latitude (required)
        - lng: user's longitude (required)
        - radius: search radius in kilometers (optional, default: 10)
        """
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        radius = request.query_params.get('radius', 50)
        
        if not latitude or not longitude:
            return Response(
                {"error": "Latitude and longitude parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            radius = float(radius)
        except ValueError:
            return Response(
                {"error": "Invalid latitude, longitude, or radius value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate nearby clinics using the Haversine formula
        clinics = self.get_queryset()
        
        # Add distance to each clinic
        nearby_clinics = []
        for clinic in clinics:
            distance = self.haversine_distance(
                latitude, longitude, 
                clinic.latitude, clinic.longitude
            )
            
            # Check if clinic is within the radius
            if distance <= radius:
                clinic.distance = distance
                nearby_clinics.append(clinic)
        
        # Sort by distance
        nearby_clinics.sort(key=lambda x: x.distance)
        
        serializer = self.get_serializer(nearby_clinics, many=True)
        return Response(serializer.data)
    
    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        Returns distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return c * r


class DentalNearmeView(viewsets.ModelViewSet):
    queryset = DentalClinic.objects.all()
    serializer_class = DentalClinicSerializer
    permission_classes = [AllowAny]
    # parser_classes = [MultiPartParser, FormParser, JSONParser]

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Find clinics within a given radius (default: 10km) of the provided coordinates.
        
        Query parameters:
        - lat: user's latitude (required)
        - lng: user's longitude (required)
        - radius: search radius in kilometers (optional, default: 10)
        """
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        radius = request.query_params.get('radius', 10)  # Default radius: 10km
        
        if not latitude or not longitude:
            return Response(
                {"error": "Latitude and longitude parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            radius = float(radius)
        except ValueError:
            return Response(
                {"error": "Invalid latitude, longitude, or radius value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate nearby clinics using the Haversine formula
        clinics = self.get_queryset()
        
        # Add distance to each clinic
        nearby_clinics = []
        for clinic in clinics:
            distance = self.haversine_distance(
                latitude, longitude, 
                clinic.latitude, clinic.longitude
            )
            
            # Check if clinic is within the radius
            if distance <= radius:
                clinic.distance = distance
                nearby_clinics.append(clinic)
        
        # Sort by distance
        nearby_clinics.sort(key=lambda x: x.distance)
        
        serializer = self.get_serializer(nearby_clinics, many=True)
        return Response(serializer.data)
    
    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        Returns distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        
        return c * r





class VisitedEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
            answers = request.data.get("answers")
            print("answers: ", answers)

            if not answers or "email" not in answers:
                return Response({"error": "Email is required"}, status=400)

            email = answers["email"]

            # Save or update to DB
            obj, created = VisitedUserData.objects.update_or_create(
                email=email,
                defaults={
                    "emergency": answers.get("emergency", ""),
                    "factors": answers.get("factors", []),
                    "lastVisit": answers.get("lastVisit", ""),
                    "anxiety": answers.get("anxiety", ""),
                    "timePreference": answers.get("timePreference", []),
                    "hasInsurance": answers.get("hasInsurance", ""),
                    "insuranceProvider": answers.get("insuranceProvider", ""),
                    "paymentOption": answers.get("paymentOption", ""),
                }
            )

            # Forward to external webhook
            try:
                webhook_url = "https://services.leadconnectorhq.com/hooks/4y5GUDosyK73YqjbTlg1/webhook-trigger/a9182ada-9332-440d-92a9-4dfd675ddb0a"
                response = requests.post(webhook_url, json=answers)
                response.raise_for_status()
            except requests.RequestException as e:
                return Response({"error": "Failed to send data to webhook", "details": str(e)}, status=500)

            return Response({"message": "Data saved and forwarded successfully"})