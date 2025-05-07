from rest_framework import serializers
from .models import (
    HealthcareFacility, FacilitySchedule, FacilityImage, 
    InsuranceProvider, PatientPreferences
)
from geopy.distance import geodesic


class FacilityScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilitySchedule
        fields = ['day', 'open_time', 'close_time', 'is_early', 'is_morning', 
                  'is_noon', 'is_afternoon', 'is_evening', 'is_weekend']

class FacilityImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = FacilityImage
        fields = ['id', 'image', 'image_url']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url') and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class InsuranceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceProvider
        fields = ['id', 'name', 'is_major']


import json

class HealthcareFacilitySerializer(serializers.ModelSerializer):
    schedule = serializers.SerializerMethodField()
    images = FacilityImageSerializer(many=True, read_only=True)
    accepted_insurance_providers = InsuranceProviderSerializer(many=True, read_only=True)
    distance = serializers.SerializerMethodField()

    class Meta:
        model = HealthcareFacility
        fields = '__all__'
    
    # Other fields remain the same...
    
    def get_images(self, obj):
        request = self.context.get('request')
        image_objects = FacilityImage.objects.filter(facility=obj)
        return FacilityImageSerializer(image_objects, many=True, context={'request': request}).data
    

    def get_distance(self, obj):
        request = self.context.get('request')
        if request:
            user_lat = request.query_params.get('lat')
            user_lng = request.query_params.get('lng')
            if user_lat and user_lng:
                facility_coords = (obj.lat, obj.lng)
                user_coords = (float(user_lat), float(user_lng))
                return round(geodesic(user_coords, facility_coords).km, 2)
        return None
    
    # Update the create method
    def create(self, validated_data):
        schedule_raw = self.initial_data.get('schedule', '{}')
        try:
            schedule_data = json.loads(schedule_raw)
        except json.JSONDecodeError:
            schedule_data = {}

        image_files = self.context.get('request').FILES.getlist('images')
        insurance_ids = self.initial_data.get('accepted_insurance_providers', [])

        facility = HealthcareFacility.objects.create(**validated_data)

        for day, times in schedule_data.items():
            open_time = times.get('open', '')
            close_time = times.get('close', '')
            if open_time or close_time:
                FacilitySchedule.objects.create(
                    facility=facility,
                    day=day,
                    open_time=open_time,
                    close_time=close_time
                )

        for image_file in image_files:
            FacilityImage.objects.create(
                facility=facility,
                image=image_file
            )

        if insurance_ids:
            facility.accepted_insurance_providers.set(insurance_ids)

        return facility
    
    # Update the update method
    def update(self, instance, validated_data):
        schedule_data = self.initial_data.get('schedule', {})
        image_files = self.context.get('request').FILES.getlist('images')
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
        # Check if new images are being uploaded
        if image_files:
            # Delete existing images
            FacilityImage.objects.filter(facility=instance).delete()
            
            # Create new image entries
            for image_file in image_files:
                FacilityImage.objects.create(
                    facility=instance,
                    image=image_file
                )
            
        # Update insurance providers
        if insurance_ids:
            instance.accepted_insurance_providers.set(insurance_ids)
        
        return instance
    

    def get_schedule(self, obj):
        schedules = FacilitySchedule.objects.filter(facility=obj)
        return [
            {
                "day": schedule.day,
                "open": schedule.open_time,
                "close": schedule.close_time
            }
            for schedule in schedules
        ]
        
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