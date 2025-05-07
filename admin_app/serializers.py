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

class HealthcareFacilitySerializer(serializers.ModelSerializer):
    schedule = serializers.SerializerMethodField()
    images = FacilityImageSerializer(many=True, read_only=True)
    accepted_insurance_providers = InsuranceProviderSerializer(many=True, read_only=True)
    distance = serializers.SerializerMethodField()
    
    # Other fields remain the same...
    
    def get_images(self, obj):
        request = self.context.get('request')
        image_objects = FacilityImage.objects.filter(facility=obj)
        return FacilityImageSerializer(image_objects, many=True, context={'request': request}).data
    
    # Update the create method
    def create(self, validated_data):
        schedule_data = self.initial_data.get('schedule', {})
        image_files = self.context.get('request').FILES.getlist('images')
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
        for image_file in image_files:
            FacilityImage.objects.create(
                facility=facility,
                image=image_file
            )
            
        # Set insurance providers
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