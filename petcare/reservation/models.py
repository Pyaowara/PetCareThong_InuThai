from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from django.utils import timezone

class User(models.Model):
    ROLE_CHOICES = (
        ('staff', 'Staff'),
        ('vet', 'Veterinarian'),
        ('client', 'Client'),
    )

    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    image_key = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = 'reservation_user'


class Vaccine(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Pet(models.Model):
    class PetGender(models.Choices):
        MALE = "Male"
        FEMALE = "Female"
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=PetGender.choices, default=PetGender.MALE)
    breed = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    allergic = models.TextField(blank=True, null=True)
    marks = models.TextField(blank=True, null=True) # ลักษณะเด่น
    chronic_conditions = models.TextField(blank=True, null=True) # โรคประจำตัว
    neutered_status = models.BooleanField(default=False)
    image_key = models.CharField(max_length=255, blank=True, null=True)
    birth_date = models.DateField()
    vaccines = models.ManyToManyField(Vaccine, through='Vaccinated', related_name='pets')

    def __str__(self):
        return f"{self.name} ({self.user.full_name})"


class Vaccinated(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine = models.ForeignKey(Vaccine, on_delete=models.CASCADE, related_name='vaccinations')
    remarks = models.TextField(blank=True, null=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.pet.name} - {self.vaccine.name} on {self.date}"


class Appointment(models.Model):
    class AppointmentStatus(models.TextChoices):
        BOOKED = 'booked'
        CONFIRMED = 'confirmed'
        COMPLETED = 'completed'
        REJECTED = 'rejected'
        CANCELLED = 'cancelled'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments')
    purpose = models.TextField()
    remarks = models.TextField(blank=True, null=True)
    date = models.DateTimeField()
    status = models.CharField(
        max_length=10,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.BOOKED,
    )
    assigned_vet = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vet_appointments'
    )
    vet_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pet.name} - {self.purpose} on {self.date.strftime('%Y-%m-%d %H:%M')}"

class Service(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

class Treatment(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='treatments')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='treatments', null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return f"{self.service} for {self.appointment.pet.name}"