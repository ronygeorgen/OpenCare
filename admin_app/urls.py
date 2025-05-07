from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HealthcareFacilityViewSet,
    InsuranceProviderViewSet, 
    PatientPreferencesViewSet
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'facilities', HealthcareFacilityViewSet, basename='facility')
router.register(r'insurance-providers', InsuranceProviderViewSet, basename='insurance')
router.register(r'patient-preferences', PatientPreferencesViewSet, basename='preferences')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]