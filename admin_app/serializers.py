from rest_framework import serializers
from .models import (
    HealthcareFacility, FacilitySchedule, FacilityImage, 
    InsuranceProvider, PatientPreferences
)

class FacilityScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilitySchedule
        fields = ['day', 'open_time', 'close_time', 'is_early', 'is_morning', 
                  'is_noon', 'is_afternoon', 'is_evening', 'is_weekend']

class FacilityImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityImage
        fields = ['id', 'image_url']

class InsuranceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceProvider
        fields = ['id', 'name', 'is_major']

class HealthcareFacilitySerializer(serializers.ModelSerializer):
    schedule = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    accepted_insurance_providers = InsuranceProviderSerializer(many=True, read_only=True)
    distance = serializers.SerializerMethodField()
    
    class Meta:
        model = HealthcareFacility
        fields = [
            'id', 'name', 'description', 'location', 'lat', 'lng', 
            'place_id', 'schedule', 'images', 'provides_new_patient_exam',
            'treats_toothache', 'treats_sensitive_gums', 'treats_tmj', 
            'provides_night_guard', 'provides_fillings', 'repairs_chipped_teeth',
            'provides_root_canal', 'provides_new_crown', 'repairs_loose_crown',
            'replaces_lost_crown', 'extracts_wisdom_teeth', 'extracts_non_wisdom_teeth',
            'treats_missing_tooth', 'provides_implants', 'provides_bridge_dentures',
            'provides_new_retainer', 'repairs_broken_retainer', 'provides_braces_invisalign',
            'provides_whitening', 'provides_veneers', 'accepted_insurance_providers',
            'rating', 'modern_facility', 'dentist_experience_years', 'distance'
        ]
    
    def get_schedule(self, obj):
        schedule_data = {}
        schedules = FacilitySchedule.objects.filter(facility=obj)
        
        for schedule in schedules:
            schedule_data[schedule.day] = {
                'open': schedule.open_time,
                'close': schedule.close_time
            }
        
        return schedule_data
    
    def get_images(self, obj):
        image_objects = FacilityImage.objects.filter(facility=obj)
        return [image.image_url for image in image_objects]
    
    def get_distance(self, obj):
        # Get the search coordinates from the context if available
        request = self.context.get('request')
        if request and request.query_params.get('lat') and request.query_params.get('lng'):
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
            # This would be replaced with actual distance calculation
            # In a real implementation, you'd typically use PostGIS or
            # a calculated field from a geospatial query
            if hasattr(obj, 'distance'):
                return obj.distance
            else:
                return obj.get_distance(lat, lng)
        return None
    
    def create(self, validated_data):
        schedule_data = self.initial_data.get('schedule', {})
        images_data = self.initial_data.get('images', [])
        insurance_ids = self.initial_data.get('accepted_insurance_providers', [])
        
        # Create healthcare facility
        facility = HealthcareFacility.objects.create(**validated_data)
        
        # Create schedule entries for each day
        for day, times in schedule_data.items():
            open_time = times.get('open', '')
            close_time = times.get('close', '')
            
            # Only create entries if at least one time is set
            if open_time or close_time:
                FacilitySchedule.objects.create(
                    facility=facility,
                    day=day,
                    open_time=open_time,
                    close_time=close_time
                )
        
        # Create image entries
        for image_url in images_data:
            FacilityImage.objects.create(
                facility=facility,
                image_url=image_url
            )
            
        # Set insurance providers
        if insurance_ids:
            facility.accepted_insurance_providers.set(insurance_ids)
        
        return facility
    
    def update(self, instance, validated_data):
        schedule_data = self.initial_data.get('schedule', {})
        images_data = self.initial_data.get('images', [])
        insurance_ids = self.initial_data.get('accepted_insurance_providers', [])
        
        # Update facility fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update schedules
        # First, delete existing schedules
        FacilitySchedule.objects.filter(facility=instance).delete()
        
        # Create new schedule entries
        for day, times in schedule_data.items():
            open_time = times.get('open', '')
            close_time = times.get('close', '')
            
            # Only create entries if at least one time is set
            if open_time or close_time:
                FacilitySchedule.objects.create(
                    facility=instance,
                    day=day,
                    open_time=open_time,
                    close_time=close_time
                )
        
        # Update images
        # First, delete existing images
        FacilityImage.objects.filter(facility=instance).delete()
        
        # Create new image entries
        for image_url in images_data:
            FacilityImage.objects.create(
                facility=instance,
                image_url=image_url
            )
            
        # Update insurance providers
        if insurance_ids:
            instance.accepted_insurance_providers.set(insurance_ids)
        
        return instance


class PatientPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientPreferences
        fields = '__all__'
        
    def create(self, validated_data):
        # Get the current user if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            
        return super().create(validated_data)