from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db.models import F, Func
from django.conf import settings
import os
from datetime import time

User = get_user_model()

class HealthcareFacility(models.Model):
    """Model for healthcare facilities."""
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=500)
    lat = models.FloatField()
    lng = models.FloatField()
    place_id = models.CharField(max_length=255)
    
    # Services offered by the facility
    provides_new_patient_exam = models.BooleanField(default=True, null=True, blank=True)
    
    # Dental Issues
    treats_toothache = models.BooleanField(default=True, null=True, blank=True)
    treats_sensitive_gums = models.BooleanField(default=True, null=True, blank=True)
    treats_tmj = models.BooleanField(default=True, null=True, blank=True)
    provides_night_guard = models.BooleanField(default=True, null=True, blank=True)
    
    # Tooth Repair
    provides_fillings = models.BooleanField(default=True, null=True, blank=True)
    repairs_chipped_teeth = models.BooleanField(default=True, null=True, blank=True)
    provides_root_canal = models.BooleanField(default=True, null=True, blank=True)
    provides_new_crown = models.BooleanField(default=True, null=True, blank=True)
    repairs_loose_crown = models.BooleanField(default=True, null=True, blank=True)
    replaces_lost_crown = models.BooleanField(default=True, null=True, blank=True)
    
    # Tooth Extraction/Replacement
    extracts_wisdom_teeth = models.BooleanField(default=True, null=True, blank=True)
    extracts_non_wisdom_teeth = models.BooleanField(default=True, null=True, blank=True)
    treats_missing_tooth = models.BooleanField(default=True, null=True, blank=True)
    provides_implants = models.BooleanField(default=True, null=True, blank=True)
    provides_bridge_dentures = models.BooleanField(default=True, null=True, blank=True)
    
    # Orthodontics
    provides_new_retainer = models.BooleanField(default=True, null=True, blank=True)
    repairs_broken_retainer = models.BooleanField(default=True, null=True, blank=True)
    provides_braces_invisalign = models.BooleanField(default=True, null=True, blank=True)
    
    # Cosmetic
    provides_whitening = models.BooleanField(default=True, null=True, blank=True)
    provides_veneers = models.BooleanField(default=True, null=True, blank=True)
    
    # Insurance providers accepted
    accepted_insurance_providers = models.ManyToManyField('InsuranceProvider', blank=True)
    
    # Operating hours handled by FacilitySchedule
    
    # Quality factors
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0, null=True, blank=True  )
    modern_facility = models.BooleanField(default=False, null=True, blank=True)
    dentist_experience_years = models.IntegerField(default=0, null=True, blank=True  )
  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Healthcare Facility"
        verbose_name_plural = "Healthcare Facilities"
        
    def get_distance(self, lat, lng):
        """
        Calculate distance between facility and provided coordinates using Haversine formula.
        This is a placeholder for the actual implementation.
        """
        # Actual implementation would use something like PostGIS's ST_Distance_Sphere
        # For now, we'll assume this will be handled by a database function or annotation
        return 0


class FacilitySchedule(models.Model):
    """Model for healthcare facility operating hours."""
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    TIME_SLOTS = [
        ('early', 'Early (Before 9am)'),
        ('morning', 'Morning (9am - 12pm)'),
        ('noon', 'Noon (12pm - 2pm)'),
        ('afternoon', 'Afternoon (2pm - 5pm)'),
        ('evening', 'Evening (After 5pm)'),
        ('weekend', 'Weekend (Sat - Sun)'),
    ]

    facility = models.ForeignKey(HealthcareFacility, on_delete=models.CASCADE, related_name='schedules')
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    open_time = models.CharField(max_length=5, blank=True)  # Format: "HH:MM"
    close_time = models.CharField(max_length=5, blank=True)  # Format: "HH:MM"
    
    # Time slot categorization for easier filtering
    is_early = models.BooleanField(default=False, null=True, blank=True)  # Before 9am
    is_morning = models.BooleanField(default=False, null=True, blank=True)  # 9am - 12pm
    is_noon = models.BooleanField(default=False, null=True, blank=True)  # 12pm - 2pm
    is_afternoon = models.BooleanField(default=False, null=True, blank=True)  # 2pm - 5pm
    is_evening = models.BooleanField(default=False, null=True, blank=True)  # After 5pm
    is_weekend = models.BooleanField(default=False, null=True, blank=True)  # Sat or Sun
    
    def save(self, *args, **kwargs):
        # Auto-calculate time slot booleans based on open and close times
        # and day of the week
        if self.open_time and self.close_time:
            self.is_early = self.open_time < "09:00"
            self.is_morning = (self.open_time < "12:00" and self.close_time > "09:00")
            self.is_noon = (self.open_time < "14:00" and self.close_time > "12:00")
            self.is_afternoon = (self.open_time < "17:00" and self.close_time > "14:00")
            self.is_evening = self.close_time > "17:00"
        
        self.is_weekend = self.day in ["Saturday", "Sunday"]
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.facility.name} - {self.day}"

    class Meta:
        unique_together = ('facility', 'day')
        verbose_name = "Facility Schedule"
        verbose_name_plural = "Facility Schedules"


def facility_image_path(instance, filename):
    """Function to determine the file path for facility images"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Create filename format: facility_id-timestamp.extension
    filename = f'{instance.facility.id}-{int(time.time())}.{ext}'
    # Return the complete path
    return os.path.join('facility_images', filename)

class FacilityImage(models.Model):
    """Model for healthcare facility images."""
    facility = models.ForeignKey(HealthcareFacility, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=facility_image_path)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.facility.name}"

    class Meta:
        verbose_name = "Facility Image"
        verbose_name_plural = "Facility Images"


class InsuranceProvider(models.Model):
    """Model for insurance providers."""
    name = models.CharField(max_length=255)
    is_major = models.BooleanField(default=False, null=True, blank=True)  # True for commonly used providers

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Insurance Provider"
        verbose_name_plural = "Insurance Providers"


class PatientPreferences(models.Model):
    """Model to store patient preferences for finding a healthcare facility."""
    CARE_TYPE_CHOICES = [
        ('ongoing', 'Looking for ongoing care'),
        ('one_time', 'One-time visit'),
    ]
    
    DENTAL_COMFORT_CHOICES = [
        ('committed', 'Committed'),
        ('neutral', 'Neutral'),
        ('uninspired', 'Uninspired'),
    ]
    
    LAST_VISIT_CHOICES = [
        ('less_than_1_year', 'Less than 1 year'),
        ('1_to_2_years', '1 to 2 years'),
        ('more_than_2_years', 'More than 2 years'),
        ('never', 'Never visited'),
    ]
    
    NERVOUSNESS_CHOICES = [
        ('not_nervous', 'Not at all nervous'),
        ('little_nervous', 'A little nervous'),
        ('moderately_nervous', 'Moderately nervous'),
        ('very_nervous', 'Very nervous'),
        ('extremely_nervous', 'Extremely nervous'),
    ]
    
    URGENCY_CHOICES = [
        ('asap', 'As soon as possible'),
        ('within_1_week', 'Within 1 week'),
        ('within_2_weeks', 'Within 2 weeks'),
        ('more_than_2_weeks', 'In more than 2 weeks'),
    ]
    
    # User connection (optional, for logged-in users)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Basic preferences
    email = models.EmailField(blank=True, null=True)
    care_type = models.CharField(max_length=20, choices=CARE_TYPE_CHOICES)
    
    # Location
    search_location = models.CharField(max_length=500)
    search_lat = models.FloatField()
    search_lng = models.FloatField()
    
    # Treatment preferences
    new_patient_exam = models.BooleanField(default=False, null=True, blank=True)
    
    # Specific concerns
    concern_toothache = models.BooleanField(default=False, null=True, blank=True)
    concern_sensitive_gums = models.BooleanField(default=False, null=True, blank=True)
    concern_tmj = models.BooleanField(default=False, null=True, blank=True)
    concern_night_guard = models.BooleanField(default=False, null=True, blank=True)
    
    concern_cavity = models.BooleanField(default=False, null=True, blank=True)
    concern_chipped_tooth = models.BooleanField(default=False, null=True, blank=True)
    concern_root_canal = models.BooleanField(default=False, null=True, blank=True)
    concern_new_crown = models.BooleanField(default=False, null=True, blank=True)
    concern_loose_crown = models.BooleanField(default=False, null=True, blank=True)
    concern_lost_crown = models.BooleanField(default=False, null=True, blank=True)
    
    concern_wisdom_extraction = models.BooleanField(default=False, null=True, blank=True)
    concern_tooth_extraction = models.BooleanField(default=False, null=True, blank=True)
    concern_missing_tooth = models.BooleanField(default=False, null=True, blank=True)
    concern_implant = models.BooleanField(default=False, null=True, blank=True)
    concern_bridge_dentures = models.BooleanField(default=False, null=True, blank=True)
    
    concern_new_retainer = models.BooleanField(default=False, null=True, blank=True)
    concern_broken_retainer = models.BooleanField(default=False, null=True, blank=True)
    concern_braces_invisalign = models.BooleanField(default=False, null=True, blank=True)
    
    concern_whitening = models.BooleanField(default=False, null=True, blank=True)
    concern_veneers = models.BooleanField(default=False, null=True, blank=True)
    
    other_concerns = models.TextField(blank=True)
    
    # Dental wellness feeling
    dental_wellness_feeling = models.CharField(max_length=20, choices=DENTAL_COMFORT_CHOICES, blank=True, null=True)
    
    # Important factors
    important_rating = models.BooleanField(default=False, null=True, blank=True)
    important_location = models.BooleanField(default=False, null=True, blank=True)
    important_modern_practice = models.BooleanField(default=False, null=True, blank=True)
    important_insurance = models.BooleanField(default=False, null=True, blank=True)
    important_schedule = models.BooleanField(default=False, null=True, blank=True)
    important_experience = models.BooleanField(default=False, null=True, blank=True)
    important_cost = models.BooleanField(default=False, null=True, blank=True)
    
    # Last visit
    last_visit = models.CharField(max_length=20, choices=LAST_VISIT_CHOICES, blank=True, null=True)
    
    # Nervousness
    nervousness = models.CharField(max_length=20, choices=NERVOUSNESS_CHOICES, blank=True, null=True)
    
    # Preferred time slots
    prefers_early = models.BooleanField(default=False, null=True, blank=True)
    prefers_morning = models.BooleanField(default=False, null=True, blank=True)
    prefers_noon = models.BooleanField(default=False, null=True, blank=True)
    prefers_afternoon = models.BooleanField(default=False, null=True, blank=True)
    prefers_evening = models.BooleanField(default=False, null=True, blank=True)
    prefers_weekend = models.BooleanField(default=False, null=True, blank=True)
    
    # Urgency
    visit_urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, blank=True, null=True)
    
    # Insurance
    has_insurance = models.BooleanField(default=False, null=True, blank=True)
    insurance_provider = models.ForeignKey(InsuranceProvider, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Social assistance
    using_social_assistance = models.BooleanField(default=False, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Preferences {self.id} - {self.email or 'Anonymous'}"

    class Meta:
        verbose_name = "Patient Preference"
        verbose_name_plural = "Patient Preferences"