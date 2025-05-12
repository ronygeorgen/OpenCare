from rest_framework import serializers
from .models import DentalClinic, BusinessHours, ClinicImage, Review
from django.db.models import Avg

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
    
    class Meta:
        model = DentalClinic
        fields = [
            'id', 'name', 'description', 'address', 'latitude', 'longitude',
            'rating', 'phone_number', 'website', 'business_hours', 'images',
            'reviews', 'average_rating', 'distance', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'average_rating', 'distance', 'created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        return obj.reviews.aggregate(Avg('rating'))['rating__avg']
    
    def get_distance(self, obj):
        # This field will be populated by the view when needed
        return getattr(obj, 'distance', None)
    
    def create(self, validated_data):
        business_hours_data = validated_data.pop('business_hours', [])
        images_data = validated_data.pop('images', [])
        reviews_data = validated_data.pop('reviews', [])
        
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
        business_hours_data = validated_data.pop('business_hours', None)
        images_data = validated_data.pop('images', None)
        reviews_data = validated_data.pop('reviews', None)
        
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