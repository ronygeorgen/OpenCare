import logging
from django.db.models import Q, F, ExpressionWrapper, FloatField
from django.db.models.functions import Power, Sqrt
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .models import HealthcareFacility, InsuranceProvider, PatientPreferences
from .serializers import (
    HealthcareFacilitySerializer, InsuranceProviderSerializer,
    PatientPreferencesSerializer
)

logger = logging.getLogger(__name__)

class HealthcareFacilityViewSet(viewsets.ModelViewSet):
    """API endpoint for managing healthcare facilities."""
    
    queryset = HealthcareFacility.objects.all()
    serializer_class = HealthcareFacilitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'location']
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        Admin permission required for create, update, delete operations.
        Allow any for list and retrieve.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        elif self.action in ['list', 'retrieve', 'search_nearby']:
            self.permission_classes = [AllowAny]
        return super().get_permissions()
    
    def get_queryset(self):
        """
        Optionally restricts the returned facilities based on query parameters.
        """
        queryset = HealthcareFacility.objects.all()
        
        # Basic location filtering
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        max_distance = self.request.query_params.get('radius', 20)  # Default 20km radius
        
        if lat and lng:
            # We'll use the Haversine formula to calculate distance
            # This is a simplified implementation for demonstration
            # In production, you would use PostGIS or a similar geospatial database extension
            lat = float(lat)
            lng = float(lng)
            max_distance = float(max_distance)
            
            # The Haversine formula using Django ORM expressions
            # This approximates the distance calculation without requiring PostGIS
            # Note: For real-world use, PostGIS would be much more efficient
            lat_radians = lat * 0.0174532925  # lat in radians (lat * π/180)
            
            # We're calculating approximately: 
            # 6371 * 2 * asin(sqrt(sin²((lat2-lat1)/2) + cos(lat1) * cos(lat2) * sin²((lon2-lon1)/2)))
            # But using ORM-compatible simplifications
            
            # This is a very simplified calculation - in production, use PostGIS
            distance_expr = ExpressionWrapper(
                Sqrt(
                    Power(F('lat') - lat, 2) + 
                    Power(F('lng') - lng, 2)
                ) * 111.32,  # rough conversion to km
                output_field=FloatField()
            )
            
            queryset = queryset.annotate(distance=distance_expr).filter(distance__lte=max_distance)
            queryset = queryset.order_by('distance')
        
        # Treatment filters
        # Common dental issues
        toothache = self.request.query_params.get('toothache')
        sensitive_gums = self.request.query_params.get('sensitive_gums')
        tmj = self.request.query_params.get('tmj')
        night_guard = self.request.query_params.get('night_guard')
        
        if toothache == 'true':
            queryset = queryset.filter(treats_toothache=True)
        if sensitive_gums == 'true':
            queryset = queryset.filter(treats_sensitive_gums=True)
        if tmj == 'true':
            queryset = queryset.filter(treats_tmj=True)
        if night_guard == 'true':
            queryset = queryset.filter(provides_night_guard=True)
        
        # Tooth repair
        cavity = self.request.query_params.get('cavity')
        chipped_tooth = self.request.query_params.get('chipped_tooth')
        root_canal = self.request.query_params.get('root_canal')
        new_crown = self.request.query_params.get('new_crown')
        loose_crown = self.request.query_params.get('loose_crown')
        lost_crown = self.request.query_params.get('lost_crown')
        
        if cavity == 'true':
            queryset = queryset.filter(provides_fillings=True)
        if chipped_tooth == 'true':
            queryset = queryset.filter(repairs_chipped_teeth=True)
        if root_canal == 'true':
            queryset = queryset.filter(provides_root_canal=True)
        if new_crown == 'true':
            queryset = queryset.filter(provides_new_crown=True)
        if loose_crown == 'true':
            queryset = queryset.filter(repairs_loose_crown=True)
        if lost_crown == 'true':
            queryset = queryset.filter(replaces_lost_crown=True)
        
        # Tooth extraction / replacement
        wisdom_extraction = self.request.query_params.get('wisdom_extraction')
        tooth_extraction = self.request.query_params.get('tooth_extraction')
        missing_tooth = self.request.query_params.get('missing_tooth')
        implant = self.request.query_params.get('implant')
        bridge_dentures = self.request.query_params.get('bridge_dentures')
        
        if wisdom_extraction == 'true':
            queryset = queryset.filter(extracts_wisdom_teeth=True)
        if tooth_extraction == 'true':
            queryset = queryset.filter(extracts_non_wisdom_teeth=True)
        if missing_tooth == 'true':
            queryset = queryset.filter(treats_missing_tooth=True)
        if implant == 'true':
            queryset = queryset.filter(provides_implants=True)
        if bridge_dentures == 'true':
            queryset = queryset.filter(provides_bridge_dentures=True)
        
        # Orthodontics
        new_retainer = self.request.query_params.get('new_retainer')
        broken_retainer = self.request.query_params.get('broken_retainer')
        braces_invisalign = self.request.query_params.get('braces_invisalign')
        
        if new_retainer == 'true':
            queryset = queryset.filter(provides_new_retainer=True)
        if broken_retainer == 'true':
            queryset = queryset.filter(repairs_broken_retainer=True)
        if braces_invisalign == 'true':
            queryset = queryset.filter(provides_braces_invisalign=True)
        
        # Cosmetic
        whitening = self.request.query_params.get('whitening')
        veneers = self.request.query_params.get('veneers')
        
        if whitening == 'true':
            queryset = queryset.filter(provides_whitening=True)
        if veneers == 'true':
            queryset = queryset.filter(provides_veneers=True)
        
        # Insurance provider
        insurance_provider_id = self.request.query_params.get('insurance_provider')
        if insurance_provider_id:
            queryset = queryset.filter(accepted_insurance_providers__id=insurance_provider_id)
        
        # Important factors
        high_rating = self.request.query_params.get('high_rating')
        modern_practice = self.request.query_params.get('modern_practice')
        experienced_dentist = self.request.query_params.get('experienced_dentist')
        
        if high_rating == 'true':
            queryset = queryset.filter(rating__gte=4.0)
        if modern_practice == 'true':
            queryset = queryset.filter(modern_facility=True)
        if experienced_dentist == 'true':
            queryset = queryset.filter(dentist_experience_years__gte=5)
        
        # Schedule preferences
        early = self.request.query_params.get('early')
        morning = self.request.query_params.get('morning')
        noon = self.request.query_params.get('noon')
        afternoon = self.request.query_params.get('afternoon')
        evening = self.request.query_params.get('evening')
        weekend = self.request.query_params.get('weekend')
        
        schedule_filters = Q()
        
        if early == 'true':
            schedule_filters |= Q(schedules__is_early=True)
        if morning == 'true':
            schedule_filters |= Q(schedules__is_morning=True)
        if noon == 'true':
            schedule_filters |= Q(schedules__is_noon=True)
        if afternoon == 'true':
            schedule_filters |= Q(schedules__is_afternoon=True)
        if evening == 'true':
            schedule_filters |= Q(schedules__is_evening=True)
        if weekend == 'true':
            schedule_filters |= Q(schedules__is_weekend=True)
        
        if schedule_filters:
            queryset = queryset.filter(schedule_filters).distinct()
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new healthcare facility."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update an existing healthcare facility."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, *args, **kwargs):
        """Partially update an existing healthcare facility."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='search-nearby')
    def search_nearby(self, request):
        """
        Search for nearby facilities with filtering based on patient preferences.
        This endpoint combines location search with filter criteria.
        """
        # Get location parameters
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        if not lat or not lng:
            return Response(
                {"error": "Location coordinates (lat, lng) are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use the filtering logic from get_queryset
        queryset = self.get_queryset()
        
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='find-match')
    def find_match(self, request):
        """
        Find matching facilities based on complete patient preferences.
        This endpoint saves the patient preferences and returns matching facilities.
        """
        # First, save the patient preferences
        pref_serializer = PatientPreferencesSerializer(data=request.data, context={'request': request})
        if pref_serializer.is_valid():
            preferences = pref_serializer.save()
            
            # Build query parameters from preferences
            query_params = {}
            
            # Location
            query_params['lat'] = preferences.search_lat
            query_params['lng'] = preferences.search_lng
            
            # Treatment preferences - Common dental issues
            if preferences.concern_toothache:
                query_params['toothache'] = 'true'
            if preferences.concern_sensitive_gums:
                query_params['sensitive_gums'] = 'true'
            if preferences.concern_tmj:
                query_params['tmj'] = 'true'
            if preferences.concern_night_guard:
                query_params['night_guard'] = 'true'
                
            # Tooth repair
            if preferences.concern_cavity:
                query_params['cavity'] = 'true'
            if preferences.concern_chipped_tooth:
                query_params['chipped_tooth'] = 'true'
            if preferences.concern_root_canal:
                query_params['root_canal'] = 'true'
            if preferences.concern_new_crown:
                query_params['new_crown'] = 'true'
            if preferences.concern_loose_crown:
                query_params['loose_crown'] = 'true'
            if preferences.concern_lost_crown:
                query_params['lost_crown'] = 'true'
                
            # Tooth extraction / replacement
            if preferences.concern_wisdom_extraction:
                query_params['wisdom_extraction'] = 'true'
            if preferences.concern_tooth_extraction:
                query_params['tooth_extraction'] = 'true'
            if preferences.concern_missing_tooth:
                query_params['missing_tooth'] = 'true'
            if preferences.concern_implant:
                query_params['implant'] = 'true'
            if preferences.concern_bridge_dentures:
                query_params['bridge_dentures'] = 'true'
                
            # Orthodontics
            if preferences.concern_new_retainer:
                query_params['new_retainer'] = 'true'
            if preferences.concern_broken_retainer:
                query_params['broken_retainer'] = 'true'
            if preferences.concern_braces_invisalign:
                query_params['braces_invisalign'] = 'true'
                
            # Cosmetic
            if preferences.concern_whitening:
                query_params['whitening'] = 'true'
            if preferences.concern_veneers:
                query_params['veneers'] = 'true'
                
            # Insurance
            if preferences.has_insurance and preferences.insurance_provider:
                query_params['insurance_provider'] = preferences.insurance_provider.id
                
            # Important factors
            if preferences.important_rating:
                query_params['high_rating'] = 'true'
            if preferences.important_modern_practice:
                query_params['modern_practice'] = 'true'
            if preferences.important_experience:
                query_params['experienced_dentist'] = 'true'
                
            # Schedule preferences
            if preferences.prefers_early:
                query_params['early'] = 'true'
            if preferences.prefers_morning:
                query_params['morning'] = 'true'
            if preferences.prefers_noon:
                query_params['noon'] = 'true'
            if preferences.prefers_afternoon:
                query_params['afternoon'] = 'true'
            if preferences.prefers_evening:
                query_params['evening'] = 'true'
            if preferences.prefers_weekend:
                query_params['weekend'] = 'true'
            
            # Create a new request with our query parameters
            new_request = request._request
            new_request.query_params = query_params
            request._request = new_request
            
            # Use the existing search_nearby action
            return self.search_nearby(request)
        
        return Response(pref_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InsuranceProviderViewSet(viewsets.ModelViewSet):
    """API endpoint for managing insurance providers."""
    
    queryset = InsuranceProvider.objects.all()
    serializer_class = InsuranceProviderSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        Admin permission required for create, update, delete operations.
        Allow any for list and retrieve.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        elif self.action in ['list', 'retrieve', 'get_major_providers']:
            self.permission_classes = [AllowAny]
        return super().get_permissions()
    
    def get_queryset(self):
        """
        Optionally restricts the returned providers based on query parameters.
        """
        queryset = InsuranceProvider.objects.all()
        
        # Filter by major provider
        is_major = self.request.query_params.get('is_major')
        if is_major == 'true':
            queryset = queryset.filter(is_major=True)
            
        return queryset.order_by('name')
    
    @action(detail=False, methods=['get'], url_path='major')
    def get_major_providers(self, request):
        """
        Get a list of major insurance providers.
        """
        major_providers = InsuranceProvider.objects.filter(is_major=True).order_by('name')
        serializer = self.get_serializer(major_providers, many=True)
        return Response(serializer.data)


class PatientPreferencesViewSet(viewsets.ModelViewSet):
    """API endpoint for managing patient preferences."""
    
    queryset = PatientPreferences.objects.all()
    serializer_class = PatientPreferencesSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['create']:
            self.permission_classes = [AllowAny]
        return super().get_permissions()
    
    def get_queryset(self):
        """
        Only return preferences belonging to the current user.
        Admin users can see all preferences.
        """
        if self.request.user.is_staff:
            return PatientPreferences.objects.all()
        return PatientPreferences.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create patient preferences and return matching facilities."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            preferences = serializer.save()
            
            # Return the created preferences
            response_data = {
                'preferences': serializer.data,
                'message': 'Patient preferences saved successfully.'
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='my-preferences')
    def my_preferences(self, request):
        """
        Get the preferences for the current logged-in user.
        """
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        preferences = PatientPreferences.objects.filter(user=request.user).order_by('-created_at').first()
        
        if not preferences:
            return Response(
                {"message": "No preferences found for this user"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)