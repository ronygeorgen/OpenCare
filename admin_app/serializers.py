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
    business_hours_json = serializers.CharField(write_only=True, required=False)
    reviews_json = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = DentalClinic
        fields = [
            'id', 'name', 'description', 'address', 'latitude', 'longitude',
            'rating', 'phone_number', 'website', 'business_hours', 'images',
            'reviews', 'average_rating', 'distance', 'created_at', 'updated_at',
            'business_hours_json', 'reviews_json'
        ]
        read_only_fields = ['id', 'average_rating', 'distance', 'created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        return obj.reviews.aggregate(Avg('rating'))['rating__avg']
    
    def get_distance(self, obj):
        # This field will be populated by the view when needed
        return getattr(obj, 'distance', None)
    
    def _extract_files_from_request(self, validated_data):
        """Extract image data from request data"""
        request = self.context.get('request')
        images_data = []
        
        if not request:
            return images_data
            
        # Look for image data in the format images[0][field_name]
        image_index = 0
        while True:
            image_data = {}
            has_image_data = False
            
            # Check for each possible image field in the request
            for field in ['image_file', 'image_url', 'caption', 'is_primary']:
                key = f'images[{image_index}][{field}]'
                if key in request.data:
                    image_data[field] = request.data[key]
                    has_image_data = True
            
            # If is_primary is a string 'true', convert to boolean True
            if 'is_primary' in image_data and image_data['is_primary'] in ['true', 'True']:
                image_data['is_primary'] = True
                
            # If no more image data is found, break the loop
            if not has_image_data:
                break
                
            # Add this image data to our collection and continue to next index
            if image_data:
                images_data.append(image_data)
            image_index += 1
            
        return images_data
    
    def create(self, validated_data):
        # Handle JSON string fields if provided
        business_hours_data = []
        if 'business_hours_json' in validated_data:
            business_hours_json = validated_data.pop('business_hours_json')
            try:
                business_hours_data = json.loads(business_hours_json)
            except (json.JSONDecodeError, TypeError):
                pass
        elif 'business_hours' in validated_data:
            business_hours_data = validated_data.pop('business_hours', [])
            
        reviews_data = []
        if 'reviews_json' in validated_data:
            reviews_json = validated_data.pop('reviews_json')
            try:
                reviews_data = json.loads(reviews_json)
            except (json.JSONDecodeError, TypeError):
                pass
        elif 'reviews' in validated_data:
            reviews_data = validated_data.pop('reviews', [])
        
        # Extract image data from the request
        images_data = self._extract_files_from_request(validated_data)
        
        # If no images found in request format, check if they exist in validated_data
        if not images_data and 'images' in validated_data:
            images_data = validated_data.pop('images', [])
        
        # Make sure to remove any direct 'images' from validated_data to avoid TypeError
        if 'images' in validated_data:
            validated_data.pop('images')
        
        print(f"Images data: {images_data}")
        print(f"Reviews data: {reviews_data}")
        print(f"Business hours data: {business_hours_data}")
        
        clinic = DentalClinic.objects.create(**validated_data)
        
        # Create business hours
        for hours_data in business_hours_data:
            BusinessHours.objects.create(clinic=clinic, **hours_data)
        
        # Create images
        for image_data in images_data:
            ClinicImage.objects.create(clinic=clinic, **image_data)
        
        # Create reviews
        for review_data in reviews_data:
            Review.objects.create(clinic=clinic, **review_data)
        
        return clinic
    
    def update(self, instance, validated_data):
        # Handle JSON string fields if provided
        business_hours_data = None
        if 'business_hours_json' in validated_data:
            business_hours_json = validated_data.pop('business_hours_json')
            try:
                business_hours_data = json.loads(business_hours_json)
            except (json.JSONDecodeError, TypeError):
                pass
        elif 'business_hours' in validated_data:
            business_hours_data = validated_data.pop('business_hours', None)
            
        reviews_data = None
        if 'reviews_json' in validated_data:
            reviews_json = validated_data.pop('reviews_json')
            try:
                reviews_data = json.loads(reviews_json)
            except (json.JSONDecodeError, TypeError):
                pass
        elif 'reviews' in validated_data:
            reviews_data = validated_data.pop('reviews', None)
        
        # Extract image data from the request
        images_data = self._extract_files_from_request(validated_data)
        
        # If no images found in request format, check if they exist in validated_data
        if not images_data and 'images' in validated_data:
            images_data = validated_data.pop('images', None)
        
        # Make sure to remove any direct 'images' from validated_data to avoid TypeError
        if 'images' in validated_data:
            validated_data.pop('images')
        
        # Update clinic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update business hours if provided
        if business_hours_data is not None:
            # Remove existing hours
            instance.business_hours.all().delete()
            # Create new hours
            for hours_data in business_hours_data:
                BusinessHours.objects.create(clinic=instance, **hours_data)
        
        # Update images if provided
        if images_data is not None:
            # Handle image updates (we'll keep existing images and add new ones)
            for image_data in images_data:
                ClinicImage.objects.create(clinic=instance, **image_data)
        
        # Update reviews if provided
        if reviews_data is not None:
            # Add new reviews (we don't update existing reviews)
            for review_data in reviews_data:
                Review.objects.create(clinic=instance, **review_data)
        
        return instance