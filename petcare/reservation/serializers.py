from rest_framework import serializers
from django.db import transaction
from .models import User
from .services import minio_service
import uuid
import os

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    image = serializers.ImageField(required=False, write_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'full_name', 'phone_number', 'role', 'image', 'image_url']

    def get_image_url(self, obj):
        return obj.get_image_url()

    def create(self, validated_data):
        password = validated_data.pop('password')
        image_file = validated_data.pop('image', None)

        if image_file:
            unique_filename = f"{uuid.uuid4()}{os.path.splitext(image_file.name)[1] or '.jpg'}"
            if minio_service.upload_image(image_file, unique_filename, image_file.content_type or 'image/jpeg'):
                validated_data['image_key'] = unique_filename

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def delete(self, instance):
        with transaction.atomic():
            user_id = instance.id
            user_email = instance.email
            image_key = instance.image_key
            instance.delete()

            if image_key:
                image_deleted = minio_service.delete_image(image_key)
                if not image_deleted:
                    print(f"Warning: Failed to delete image {image_key} from MinIO")
            
            return {
                'user_email': user_email,
                'user_id': user_id,
                'image_deleted': bool(image_key)
            }