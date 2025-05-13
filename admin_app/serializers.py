from rest_framework import serializers
from .models import DentalClinic, BusinessHours, ClinicImage, Review
from django.db.models import Avg
import json

class BusinessHoursSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_display', read_only=True)
    
    class Meta:
        model = BusinessHours
        fields = ['id', 'day', 'day_name', 'opening_time', 'closing_time', 'is_closed']


class ClinicImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicImage
        fields = ['id', 'image_file', 'image_url', 'caption', 'is_primary']
        read_only_fields = ['id']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'author_name', 'author_photo_url', 'rating', 'text', 'created_at']
        read_only_fields = ['id', 'created_at']


class DentalClinicSerializer(serializers.ModelSerializer):
    business_hours = BusinessHoursSerializer(many=True, required=False)
    images = ClinicImageSerializer(many=True, required=False)
    reviews = ReviewSerializer(many=True, required=False)
    average_rating = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    business_types = serializers.ListField(child=serializers.CharField(), required=False)
    
    class Meta:
        model = DentalClinic
        fields = [
            'id', 'name', 'description', 'address', 'latitude', 'longitude',
            'rating', 'phone_number', 'website', 'business_hours', 'images',
            'reviews', 'average_rating', 'distance', 'created_at', 'updated_at',
            'business_types'
        ]
        read_only_fields = ['id', 'average_rating', 'distance', 'created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        return obj.reviews.aggregate(Avg('rating'))['rating__avg']
    
    def get_distance(self, obj):
        # This field will be populated by the view when needed
        return getattr(obj, 'distance', None)
    
    def to_internal_value(self, data):
        # Convert QueryDict to proper dict
        if hasattr(data, 'getlist'):
            processed_data = {}
            for key in data:
                values = data.getlist(key)
                if len(values) == 1:
                    processed_data[key] = values[0]
                else:
                    processed_data[key] = values
        else:
            processed_data = data
            
        # Handle JSON string fields
        if 'business_hours' in processed_data:
            if isinstance(processed_data['business_hours'], str):
                try:
                    processed_data['business_hours'] = json.loads(processed_data['business_hours'])
                except (json.JSONDecodeError, TypeError):
                    pass

            if isinstance(processed_data['business_hours'], dict):
                day_name_to_int = {
                    'Monday': 0,
                    'Tuesday': 1,
                    'Wednesday': 2,
                    'Thursday': 3,
                    'Friday': 4,
                    'Saturday': 5,
                    'Sunday': 6
                }

                hours_list = []
                for day_name, times in processed_data['business_hours'].items():
                    day_int = day_name_to_int.get(day_name)
                    open_time = times.get('open') or None
                    close_time = times.get('close') or None
                    hours_list.append({
                        'day': day_int,
                        'opening_time': open_time,
                        'closing_time': close_time,
                        'is_closed': not open_time or not close_time
                    })

                processed_data['business_hours'] = hours_list

                
        if 'reviews' in processed_data and isinstance(processed_data['reviews'], str):
            try:
                processed_data['reviews'] = json.loads(processed_data['reviews'])
            except (json.JSONDecodeError, TypeError):
                pass
                
        if 'images' in processed_data and isinstance(processed_data['images'], str):
            try:
                processed_data['images'] = json.loads(processed_data['images'])
            except (json.JSONDecodeError, TypeError):
                pass
                
        if 'business_types' in processed_data and isinstance(processed_data['business_types'], str):
            try:
                processed_data['business_types'] = json.loads(processed_data['business_types'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        return super().to_internal_value(processed_data)
    
    def create(self, validated_data):
        # Extract nested data
        business_hours_data = validated_data.pop('business_hours', [])
        reviews_data = validated_data.pop('reviews', [])
        images_data = validated_data.pop('images', [])
        business_types = validated_data.pop('business_types', [])
        
        print(f"Images data (before create): {images_data}")
        print(f"Reviews data (before create): {reviews_data}")
        print(f"Business hours data (before create): {business_hours_data}")
        
        # Create the clinic
        clinic = DentalClinic.objects.create(**validated_data)
        
        # Save business types
        if business_types:
            clinic.business_types = business_types
            clinic.save()
        
        # Create business hours
        if isinstance(business_hours_data, dict):
            # Convert dict format to list format
            hours_list = []
            for day, hours in business_hours_data.items():
                hours_list.append({
                    'day_of_week': day,
                    'open_time': hours.get('open'),
                    'close_time': hours.get('close'),
                    'is_closed': not hours.get('open') or not hours.get('close')
                })
            business_hours_data = hours_list
            
        for hours_data in business_hours_data:
            BusinessHours.objects.create(clinic=clinic, **hours_data)
        
        # Create images
        for image_data in images_data:
            # If image_file is provided as string 'null', convert to None
            if 'image_file' in image_data and image_data['image_file'] == 'null':
                image_data['image_file'] = None
            ClinicImage.objects.create(clinic=clinic, **image_data)
        
        # Create reviews
        for review_data in reviews_data:
            Review.objects.create(clinic=clinic, **review_data)
        
        return clinic
    
    def update(self, instance, validated_data):
        # Extract nested data
        business_hours_data = validated_data.pop('business_hours', None)
        reviews_data = validated_data.pop('reviews', None)
        images_data = validated_data.pop('images', None)
        business_types = validated_data.pop('business_types', None)
        
        # Update clinic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update business types if provided
        if business_types is not None:
            instance.business_types = business_types
            
        instance.save()
        
        # Update business hours if provided
        if business_hours_data is not None:
            # Remove existing hours
            instance.business_hours.all().delete()
            
            # Handle different formats
            if isinstance(business_hours_data, dict):
                hours_list = []
                for day, hours in business_hours_data.items():
                    hours_list.append({
                        'day_of_week': day,
                        'open_time': hours.get('open'),
                        'close_time': hours.get('close'),
                        'is_closed': not hours.get('open') or not hours.get('close')
                    })
                business_hours_data = hours_list
                
            # Create new hours
            for hours_data in business_hours_data:
                BusinessHours.objects.create(clinic=instance, **hours_data)
        
        # Update images if provided
        if images_data is not None:
            # You might want to decide: delete existing images or just add new ones
            # For now, let's just add new ones
            for image_data in images_data:
                if 'image_file' in image_data and image_data['image_file'] == 'null':
                    image_data['image_file'] = None
                ClinicImage.objects.create(clinic=instance, **image_data)
        
        # Update reviews if provided
        if reviews_data is not None:
            # Add new reviews (we don't update existing reviews)
            for review_data in reviews_data:
                Review.objects.create(clinic=instance, **review_data)
        
        return instance