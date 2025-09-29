from rest_framework import serializers
from django.db import transaction
from .models import *
from .services import minio_service, get_user_service
import uuid
import os

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    image = serializers.ImageField(required=False, write_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'full_name', 'phone_number', 'role', 'image', 'image_url', 'active', 'created_at']

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
    
    def delete(self, instance, request=None):
        if request:
            user_service = get_user_service(request)
            user_service.check_authentication()

        with transaction.atomic():
            user_id = instance.id
            user_email = instance.email
            image_key = instance.image_key
            instance.delete()

            if image_key:
                image_deleted = minio_service.delete_image(image_key)
                if not image_deleted:
                    raise Exception("Failed to delete user image from storage")
            
            return {
                'user_email': user_email,
                'user_id': user_id,
                'image_deleted': bool(image_key)
            }

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    if not user.active:
                        raise serializers.ValidationError('User account is disabled.')
                    data['user'] = user
                    return data
                else:
                    raise serializers.ValidationError('Invalid email or password.')
            except User.DoesNotExist:
                raise serializers.ValidationError('Invalid email or password.')
        else:
            raise serializers.ValidationError('Must include email and password.')

class UserProfileSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone_number', 'role', 'active', 'created_at', 'image_url']

    def get_image_url(self, obj):
        return obj.get_image_url()

class UserUpdateSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    image = serializers.ImageField(required=False, write_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'current_password', 'full_name', 'phone_number', 'role', 'active', 'image', 'image_url']

    def get_image_url(self, obj):
        return obj.get_image_url()

    def validate(self, data):
        user = self.instance
        request = self.context.get('request')
        user_service = get_user_service(request)

        is_staff = user_service.is_staff()
        is_own_profile = str(user_service.user_id) == str(user.id)
        
        if not is_staff and not is_own_profile:
            raise serializers.ValidationError("You can only update your own profile.")

        if not is_staff:
            current_password = data.get('current_password')
            if not current_password:
                raise serializers.ValidationError("Current password is required to update your profile.")
            
            if not user.check_password(current_password):
                raise serializers.ValidationError("Current password is incorrect.")

            restricted_fields = ['role', 'active']
            for field in restricted_fields:
                if field in data:
                    del data[field]

        data.pop('current_password', None)
        
        return data

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        image_file = validated_data.pop('image', None)

        if image_file:
            if instance.image_key:
                minio_service.delete_image(instance.image_key)

            unique_filename = f"{uuid.uuid4()}{os.path.splitext(image_file.name)[1] or '.jpg'}"
            if minio_service.upload_image(image_file, unique_filename, image_file.content_type or 'image/jpeg'):
                validated_data['image_key'] = unique_filename

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        
        instance.save()
        return instance
    
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'title', 'description']

class PetSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, write_only=True)
    image_url = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    age = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Pet
        fields = [
            'id', 'user', 'name', 'gender', 'breed', 'color', 
            'allergic', 'marks', 'chronic_conditions', 'neutered_status', 
            'birth_date', 'image', 'image_url', 'age', 'owner_id'
        ]

    def get_image_url(self, obj):
        return obj.get_image_url()

    def get_age(self, obj):
        from datetime import date
        today = date.today()
        age = today.year - obj.birth_date.year - ((today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
        return age

    def create(self, validated_data):
        image_file = validated_data.pop('image', None)
        owner_id = validated_data.pop('owner_id', None)

        request = self.context.get('request')
        user_service = request.user_service

        if user_service.is_staff():
            if owner_id:
                try:
                    owner = User.objects.get(id=owner_id)
                    validated_data['user'] = owner
                except User.DoesNotExist:
                    raise serializers.ValidationError({'owner_id': 'Invalid user ID provided.'})
            else:
                validated_data['user'] = user_service.get_user()
        elif user_service.is_client():
            if owner_id and owner_id != user_service.user_id:
                raise serializers.ValidationError({'owner_id': 'Clients can only create pets for themselves.'})
            validated_data['user'] = user_service.get_user()
        else:
            raise serializers.ValidationError({'error': 'Invalid user role for pet creation.'})

        if image_file:
            unique_filename = f"pets/{uuid.uuid4()}{os.path.splitext(image_file.name)[1] or '.jpg'}"
            if minio_service.upload_image(image_file, unique_filename, image_file.content_type or 'image/jpeg'):
                validated_data['image_key'] = unique_filename

        pet = Pet.objects.create(**validated_data)
        return pet

    def update(self, instance, validated_data):
        image_file = validated_data.pop('image', None)

        if image_file:
            if instance.image_key:
                minio_service.delete_image(instance.image_key)

            unique_filename = f"pets/{uuid.uuid4()}{os.path.splitext(image_file.name)[1] or '.jpg'}"
            if minio_service.upload_image(image_file, unique_filename, image_file.content_type or 'image/jpeg'):
                validated_data['image_key'] = unique_filename

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class PetListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Pet
        fields = ['id', 'name', 'breed', 'gender', 'age', 'image_url', 'owner_name']

    def get_image_url(self, obj):
        return obj.get_image_url()

    def get_age(self, obj):
        from datetime import date
        today = date.today()
        age = today.year - obj.birth_date.year - ((today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
        return age

class VaccineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaccine
        fields = ['id', 'name', 'description']

    def validate_name(self, value):
        if Vaccine.objects.filter(name__iexact=value).exclude(id=getattr(self.instance, 'id', None)).exists():
            raise serializers.ValidationError("A vaccine with this name already exists.")
        return value

class VaccinatedSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    vaccine_name = serializers.CharField(source='vaccine.name', read_only=True)
    owner_name = serializers.CharField(source='pet.user.full_name', read_only=True)

    class Meta:
        model = Vaccinated
        fields = ['id', 'pet', 'vaccine', 'date', 'remarks', 'pet_name', 'vaccine_name', 'owner_name']

    def validate_date(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("Vaccination date cannot be in the future.")
        return value

class VaccinatedListSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    pet_breed = serializers.CharField(source='pet.breed', read_only=True)
    vaccine_name = serializers.CharField(source='vaccine.name', read_only=True)
    owner_name = serializers.CharField(source='pet.user.full_name', read_only=True)

    class Meta:
        model = Vaccinated
        fields = ['id', 'date', 'remarks', 'pet_name', 'pet_breed', 'vaccine_name', 'owner_name']

class BookAppointmentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='client'), required=False)
    class Meta:
        model = Appointment
        fields = ['id', 'user', 'pet', 'purpose', 'remarks', 'date']

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'
class AppointmentListSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    owner_name = serializers.CharField(source='user.full_name', read_only=True)
    owner_email = serializers.CharField(source='user.email', read_only=True)
    assigned_vet = serializers.CharField(source='assigned_vet.full_name', read_only=True)
    class Meta:
        model = Appointment
        fields = ['id', 'date', 'pet_name', 'owner_name', 'status', 'purpose', 'owner_email', 'assigned_vet']

class UpdateAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'assigned_vet', 'status', 'vet_note']
        
