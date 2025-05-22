from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DentalClinicViewSet, get_place_details, VisitedEmailView

router = DefaultRouter()
router.register(r'clinics', DentalClinicViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("place-details/", get_place_details, name="place-details"),
    path("add-email/", VisitedEmailView.as_view(), name="add-email"),
    
]       