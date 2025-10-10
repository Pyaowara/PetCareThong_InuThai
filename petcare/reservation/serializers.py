from rest_framework import serializers
from django.db import transaction
from .models import *
from .services import minio_service, get_user_service
import uuid
import os
from datetime import timedelta
from django.utils import timezone

"""Pattrapol Yaowaraj 66070148"""
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    image = serializers.ImageField(required=False, write_only=True)
    image_url = serializers.SerializerMethodField()
    active = serializers.BooleanField(default=True, required=False)

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
    
    def validate_birth_date(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("Birth date cannot be in the future.")
        return value

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
    owner_id = serializers.IntegerField(source='user.id', read_only=True)
    owner_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Pet
        fields = ['id', 'name', 'breed', 'gender', 'age', 'image_url', 'owner_name', 'owner_id']

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

"""End Of Pattrapol Yaowaraj 66070148"""

"""Teetat Thongkumtae 66070092"""

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'title', 'description']
    def validate_title(self, value):
        if Service.objects.filter(title__iexact=value):
            raise serializers.ValidationError(f'{value} has already used')
        elif value.lower in ['getvaccine', 'neutering/spaying', 'other']:
            raise serializers.ValidationError(f'{value} is a main service')
        return value

class BookAppointmentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='client'), required=False)
    assigned_vet = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='vet'), required=False, allow_null=True)
    class Meta:
        model = Appointment
        fields = ['id', 'user', 'pet', 'purpose', 'remarks', 'date', 'assigned_vet']
    def validate_user(self, value):
        request = self.context.get('request', None)
        user_service = getattr(request, 'user_service', None) if request else None
        if user_service:
            if user_service.is_staff():
                if not value:
                    raise serializers.ValidationError('Owner (user) is required for staff booking.')
                else:
                    if value.role != 'client':
                        raise serializers.ValidationError('Selected user is not a client.')
        return value
    def validate_date(self, value):
        appointment_time = timezone.localtime(value)
        now = timezone.localtime(timezone.now()) 
        if appointment_time < now:
            raise serializers.ValidationError("Appointment date cannot be in the past.")
        return value
    def validate_assigned_vet(self, value):
        request = self.context.get('request', None)
        user_service = getattr(request, 'user_service', None) if request else None
        if user_service:
            if user_service.is_staff():
                if not value:
                    raise serializers.ValidationError('Staff must assign a veterinarian (assigned_vet).')
                else: 
                    if value.role != 'vet':
                        raise serializers.ValidationError('Assigned user is not a veterinarian.')
            else:
                if value is not None:
                    raise serializers.ValidationError('Cannot assign a veterinarian.')
        return value

    def validate_pet(self, value):
        request = self.context.get('request', None)
        user_service = getattr(request, 'user_service', None) if request else None
        if user_service and user_service.is_staff():
            user = self.initial_data.get('user')
            if user:
                try:
                    user_obj = User.objects.get(pk=user)
                    if value.user.id != user_obj.id:
                        raise serializers.ValidationError('Pet owner does not match selected user.')
                except User.DoesNotExist:
                    raise serializers.ValidationError('Selected user does not exist.')
        return value

    def create(self, validated_data):
        request = self.context.get('request', None)
        user_service = getattr(request, 'user_service', None) if request else None
        appointment_time = timezone.localtime(validated_data['date'])
        now = timezone.localtime(timezone.now())
        if appointment_time - now < timedelta(days=3):
            raise serializers.ValidationError("You must booked appointment before appointment date for 3 day.")
        if user_service:
            if user_service.is_client():
                validated_data['user'] = user_service.get_user()
                validated_data['status'] = 'booked'
                validated_data['assigned_vet'] = None
            elif user_service.is_staff():
                if not validated_data.get('user'):
                    raise serializers.ValidationError({'user': 'Owner (user) is required for staff booking.'})
                if not validated_data.get('assigned_vet'):
                    raise serializers.ValidationError({'assigned_vet': 'Staff must assign a veterinarian (assigned_vet).'})
                validated_data['status'] = 'confirmed'

        appointment = Appointment.objects.create(**validated_data)
        return appointment

    def update(self, instance, validated_data):
        request = self.context.get('request', None)
        user_service = getattr(request, 'user_service', None) if request else None
        appointment_time = timezone.localtime(validated_data['date'])
        now = timezone.localtime(timezone.now())
        if appointment_time - now < timedelta(days=3) and appointment_time != instance.date:
            raise serializers.ValidationError("You must booked appointment before appointment date for 3 day.")
        if user_service and user_service.is_client():
            if instance.status != 'booked':
                raise serializers.ValidationError({'status': 'Client can\'t edit appoitment when status is not booked'})
            if not validated_data.get('user'):
                validated_data['user'] = user_service.get_user()
            validated_data['assigned_vet'] = None
        if user_service and user_service.is_staff():
            status = request.data.get('status') 
            if not status:
                raise serializers.ValidationError({'status': 'Staff must provide status.'})
            validated_data['status'] = status
            if status == 'confirmed' and not validated_data.get('assigned_vet'):
                raise serializers.ValidationError({'assigned_vet': 'Staff must assign a veterinarian (assigned_vet) when status is confirmed.'})


        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

class AppointmentListSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    owner_name = serializers.CharField(source='user.full_name', read_only=True)
    owner_email = serializers.CharField(source='user.email', read_only=True)
    assigned_vet = serializers.CharField(source='assigned_vet.full_name', read_only=True)
    pet_image_url = serializers.CharField(source='pet.get_image_url', read_only=True)
    pet_breed = serializers.CharField(source='pet.breed', read_only=True)
    pet_gender = serializers.CharField(source='pet.gender', read_only=True)
    pet_age = serializers.SerializerMethodField()
    def get_pet_age(self, obj):
        from datetime import date
        if obj.pet.birth_date:
            today = date.today()
            birth_date = obj.pet.birth_date
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        return None
    class Meta:
        model = Appointment
        fields = ['id', 'date', 'pet_name', 'owner_name', 'status', 'purpose', 'owner_email', 'assigned_vet', 'pet_image_url', 'pet_breed', 'pet_gender', 'pet_age']


class UpdateStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'status', 'assigned_vet']

    def validate(self, data):
        user_service = self.context.get('user_service')
        appointment = self.instance

        if user_service.is_client():
            if appointment.user != user_service.get_user():
                raise serializers.ValidationError('Permission denied.')

            if data.get('assigned_vet'):
                raise serializers.ValidationError('Clients cannot assign a vet.')

            if data.get('status') not in ['cancelled', 'booked']:
                raise serializers.ValidationError('Clients can only update status to "cancelled" or "booked".')

        elif user_service.is_staff():
            if data.get('status') == 'confirmed' and not data.get('assigned_vet'):
                raise serializers.ValidationError('Cannot confirm without assigning a vet.')
        else:
            raise serializers.ValidationError('Permission denied.')

        return data
    

class TreatmentSerializer(serializers.ModelSerializer):
    vaccine = serializers.PrimaryKeyRelatedField(queryset=Vaccine.objects.all(), required=False, allow_null=True)
    appointment = serializers.PrimaryKeyRelatedField(queryset=Appointment.objects.all(), required=False)
    
    class Meta:
        model = Treatment
        fields = ['id', 'appointment', 'description', 'service', 'vaccine']

    def create(self, validated_data):
        appointment = validated_data.get('appointment')
        service = validated_data.get('service')
        

        if not appointment:
            raise serializers.ValidationError({'appointment': 'Appointment is required for treatment.'})
        if appointment.status != 'confirmed':
            raise serializers.ValidationError({'appointment': 'Treatment can only be added to confirmed appointments.'})
        
        with transaction.atomic():
            vaccine = validated_data.get('vaccine')
            if vaccine and service.title.lower() != 'getvaccine':
                raise serializers.ValidationError({'vaccine': 'Vaccine can only be provided for "getVaccine" service.'})
            if service.title.lower() == 'getvaccine':
                if not vaccine:
                    raise serializers.ValidationError({'vaccine': 'Vaccine is required when service is "getVaccine".'})
                Vaccinated.objects.create(
                    pet=appointment.pet,
                    vaccine=vaccine,
                    date=appointment.date.date(),
                    remarks=f'Vaccination administered during appointment ({appointment.purpose}).'
                )
            if service.title.lower() == 'neutering/spaying':
                if appointment.pet.neutered_status:
                    raise serializers.ValidationError({'pet': 'Pet is already neutered/spayed.'})
                else:
                    appointment.pet.neutered_status = True
                    appointment.pet.save()
            
            treatment = Treatment.objects.create(**validated_data)
        return treatment
    

class UpdateTreatmentSerializer(serializers.Serializer):
    vet_note = serializers.CharField(required=False, allow_blank=True)
    treatment = TreatmentSerializer(many=True)
    def create(self, validated_data):
        
        vet_note = validated_data.get('vet_note', '')
        treatments_data = validated_data.get('treatment', [])
        if not treatments_data:
            raise serializers.ValidationError({'treatment': 'At least one treatment is required.'})
        appointment = Appointment.objects.get(id=self.context.get('appointment_id'))
        if appointment.status != 'confirmed':
            raise serializers.ValidationError({'appointment': 'Treatments can only be added to confirmed appointments.'})

        with transaction.atomic():
            if vet_note:
                appointment.vet_note = vet_note
                appointment.status = 'completed'
                appointment.save()

            created_treatments = []
            for treatment_data in treatments_data:
                treatment_data['appointment'] = appointment.id
                if 'service' in treatment_data and isinstance(treatment_data['service'], Service):
                    treatment_data['service'] = treatment_data['service'].id
                if 'vaccine' in treatment_data and isinstance(treatment_data['vaccine'], Vaccine):
                    treatment_data['vaccine'] = treatment_data['vaccine'].id
                treatment_serializer = TreatmentSerializer(data=treatment_data)
                treatment_serializer.is_valid(raise_exception=True)
                treatment = treatment_serializer.save()
                created_treatments.append(treatment)
            appointment.status = 'completed'
            appointment.save()

        return {
            'appointment': appointment,
            'created_treatments': created_treatments
        }
class UserHistorySerializer(serializers.ModelSerializer):
    appointment = serializers.CharField(source='appointment.purpose', read_only=True)
    service = serializers.CharField(source='service.title', read_only=True)
    pet = serializers.CharField(source='appointment.pet.name', read_only=True)
    vaccine = serializers.CharField(source='vaccine.name', read_only=True)

    class Meta:
        model = Treatment
        fields = ['id', 'appointment', 'service', 'description', 'vaccine', 'pet']