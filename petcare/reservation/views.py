from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Case, When, Value, IntegerField
from .models import *
from .serializers import *
from .services import *

class UserView(APIView):
    parser_classes = [MultiPartParser, JSONParser]
    
    def get(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            role = request.GET.get('roles')

            if not user_service.is_staff():
                return Response({'error': 'Staff access required'}, status=status.HTTP_403_FORBIDDEN)

            users = User.objects.all()
            if role and (role == "client"):
                users = users.filter(role='client')
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
class UserViewByRole(APIView):
    def get(self, request, role):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()

            
            if not user_service.is_staff():
                return Response({'error': 'Staff access required'}, status=status.HTTP_403_FORBIDDEN)

            users = User.objects.all()
            if role in ['client', 'staff', 'vet']:
                users = users.filter(role=role)
                serializer = UserSerializer(users, many=True)
                return Response(serializer.data)
            return Response({'error': f'Role {role} not found'}, status=status.HTTP_403_FORBIDDEN)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class UserDetailView(APIView):
    parser_classes = [MultiPartParser, JSONParser]
    
    def get(self, request, user_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()

            if not user_service.is_staff() and not user_service.is_vet() and str(user_service.user_id) != str(user_id):
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            user = User.objects.get(id=user_id)

            user_serializer = UserSerializer(user)

            pets = Pet.objects.filter(user=user)
            pets_serializer = PetListSerializer(pets, many=True)
            
            response_data = user_serializer.data.copy()
            response_data['pets'] = pets_serializer.data
            response_data['total_pets'] = len(pets_serializer.data)
            
            return Response(response_data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    def put(self, request, user_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            user = User.objects.get(id=user_id)
            serializer = UserUpdateSerializer(user, data=request.data, partial=True, context={'request': request})
            
            if serializer.is_valid():
                updated_user = serializer.save()
                return Response({
                    'message': 'User updated successfully',
                    'user': {
                        'id': updated_user.id,
                        'email': updated_user.email,
                        'full_name': updated_user.full_name,
                        'phone_number': updated_user.phone_number,
                        'role': updated_user.role,
                        'active': updated_user.active,
                        'image_url': updated_user.get_image_url()
                    }
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'Failed to update user',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, user_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()

            if not user_service.is_staff() and str(user_service.user_id) != str(user_id):
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            user = User.objects.get(id=user_id)
            serializer = UserSerializer(user)

            delete_info = serializer.delete(user, request)
            response_message = f'User {delete_info["user_email"]} deleted successfully'
                
            return Response({
                'message': response_message,
                'deleted_user_id': delete_info['user_id'],
                'image_deleted': delete_info['image_deleted']
            }, status=status.HTTP_200_OK)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'Failed to delete user',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            print(f"Login user: {user}")

            request.session['user_id'] = user.id
            request.session.save()
            
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'image_url': user.get_image_url()
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        request.session.flush()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

class RegisterView(APIView):
    parser_classes = [MultiPartParser, JSONParser]
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    def get(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            user = user_service.get_user()
            if not user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = UserProfileSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class ServiceView(APIView):
    parser_classes = [MultiPartParser, JSONParser]
    
    # Get all service
    def get(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            if not user_service.is_staff() and not user_service.is_vet():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            services = Service.objects.all()
            serializer = ServiceSerializer(services, many=True)
            return Response(serializer.data)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Create Service
    def post(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            if not user_service.is_staff():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            serializer = ServiceSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
class UpdateServiceView(APIView):
    # Get a service
    def get(self, request, service_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            if not user_service.is_staff():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            service = Service.objects.get(id=service_id)
            serializer = ServiceSerializer(service)
            if service:
                return Response(serializer.data)
            else:
                return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Service.DoesNotExist:
            return Response({'error': 'service not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Edit service
    def put(self, request, service_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            if not user_service.is_staff():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            service = Service.objects.get(id=service_id)
            if service.title in ['getVaccine', 'Neutering/Spaying', 'Others']:
                return Response({'error': 'Can edit service getVaccine, Neutering/Spaying and Other'}, status=status.HTTP_403_FORBIDDEN)
            serializer = ServiceSerializer(service, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': f'Update service_id {service_id} success',
                    'services': serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Service.DoesNotExist:
            return Response({'error': 'service not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'Failed to update service',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    # Delete Service
    def delete(self, request, service_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            if not user_service.is_staff():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            service = Service.objects.get(id=service_id)
            if service.title in ['getVaccine', 'Neutering/Spaying', 'Others']:
                return Response({'error': 'Can delete service getVaccine, Neutering/Spaying and Other'}, status=status.HTTP_403_FORBIDDEN)
            service_title = service.title
            service.delete()
            response_message = f'Service {service_title} deleted successfully'
            return Response({
                'message': response_message,
                'delete_service_id': service_id
            }, status=status.HTTP_200_OK)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Service.DoesNotExist:
            return Response({'error': 'service not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'Failed to delete service',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PetView(APIView):
    parser_classes = [MultiPartParser, JSONParser]

    def get(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()

            if user_service.is_staff() or user_service.is_vet():
                pets = Pet.objects.all().select_related('user')
            else:
                pets = Pet.objects.filter(user=user_service.get_user())
            
            serializer = PetListSerializer(pets, many=True)
            return Response(serializer.data)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()

            if user_service.is_vet():
                return Response({
                    'error': 'Veterinarians cannot create pet records. Please contact staff.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            request.user_service = user_service

            serializer = PetSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                pet = serializer.save()
                return Response(PetSerializer(pet).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class PetDetailView(APIView):
    parser_classes = [MultiPartParser, JSONParser]
    
    def get(self, request, pet_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            pet = Pet.objects.select_related('user').get(id=pet_id)

            if not user_service.is_staff() and pet.user != user_service.get_user() and not user_service.is_vet():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            pet_serializer = PetSerializer(pet)
            vaccinations = Vaccinated.objects.filter(pet=pet).select_related('vaccine').order_by('-date')
            vaccination_serializer = VaccinatedSerializer(vaccinations, many=True)

            response_data = pet_serializer.data.copy()
            response_data['vaccinations'] = vaccination_serializer.data
            response_data['total_vaccinations'] = len(vaccination_serializer.data)

            return Response(response_data)
        except Pet.DoesNotExist:
            return Response({'error': 'Pet not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    def put(self, request, pet_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            pet = Pet.objects.select_related('user').get(id=pet_id)

            if not user_service.is_staff() and pet.user != user_service.get_user():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = PetSerializer(pet, data=request.data, partial=True)
            if serializer.is_valid():
                pet = serializer.save()
                return Response(PetSerializer(pet).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Pet.DoesNotExist:
            return Response({'error': 'Pet not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    def delete(self, request, pet_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            pet = Pet.objects.select_related('user').get(id=pet_id)

            if not user_service.is_staff() and pet.user != user_service.get_user():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            pet_name = pet.name
            pet_owner = pet.user.full_name
            image_key = pet.image_key

            with transaction.atomic():
                pet.delete()
                if image_key:
                    image_deleted = minio_service.delete_image(image_key)
                    if not image_deleted:
                        print(f"Warning: Failed to delete pet image {image_key} from MinIO")
            
            return Response({
                'message': f'Pet {pet_name} (owner: {pet_owner}) deleted successfully',
                'pet_id': pet_id,
                'image_deleted': bool(image_key)
            }, status=status.HTTP_200_OK)
        except Pet.DoesNotExist:
            return Response({'error': 'Pet not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                'error': 'Failed to delete pet',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VaccineView(APIView):
    
    def get(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            vaccines = Vaccine.objects.all().order_by('name')
            serializer = VaccineSerializer(vaccines, many=True)
            return Response(serializer.data)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    def post(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            if user_service.is_client():
                return Response({'error': 'Staff access required'}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = VaccineSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Vaccine created successfully',
                    'vaccine': serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class VaccineDetailView(APIView):
    
    def get(self, request, vaccine_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            vaccine = Vaccine.objects.get(id=vaccine_id)
            serializer = VaccineSerializer(vaccine)
            return Response(serializer.data)
        except Vaccine.DoesNotExist:
            return Response({'error': 'Vaccine not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    def put(self, request, vaccine_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            if not user_service.is_staff() and not user_service.is_vet():
                return Response({'error': 'Staff access required'}, status=status.HTTP_403_FORBIDDEN)
            
            vaccine = Vaccine.objects.get(id=vaccine_id)
            serializer = VaccineSerializer(vaccine, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Vaccine updated successfully',
                    'vaccine': serializer.data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Vaccine.DoesNotExist:
            return Response({'error': 'Vaccine not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    def delete(self, request, vaccine_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            if not user_service.is_staff() and not user_service.is_vet():
                return Response({'error': 'Staff access required'}, status=status.HTTP_403_FORBIDDEN)
            
            vaccine = Vaccine.objects.get(id=vaccine_id)

            if vaccine.vaccinations.exists():
                return Response({
                    'error': 'Cannot delete vaccine that has vaccination records'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            vaccine_name = vaccine.name
            vaccine.delete()
            
            return Response({
                'message': f'Vaccine "{vaccine_name}" deleted successfully'
            }, status=status.HTTP_200_OK)
        except Vaccine.DoesNotExist:
            return Response({'error': 'Vaccine not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class VaccinatedView(APIView):
    
    def get(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()

            pet_id = request.GET.get('pet_id')
            vaccine_id = request.GET.get('vaccine_id')
            owner_id = request.GET.get('owner_id')

            queryset = Vaccinated.objects.select_related('pet', 'vaccine', 'pet__user').order_by('-date')

            if pet_id:
                queryset = queryset.filter(pet_id=pet_id)
            if vaccine_id:
                queryset = queryset.filter(vaccine_id=vaccine_id)
            if owner_id:
                queryset = queryset.filter(pet__user_id=owner_id)

            if not user_service.is_staff() and not user_service.is_vet():
                queryset = queryset.filter(pet__user_id=user_service.user_id)
            
            serializer = VaccinatedListSerializer(queryset, many=True)
            return Response(serializer.data)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    def post(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()

            if not user_service.is_staff() and not user_service.is_vet():
                return Response({'error': 'Staff or vet access required to create vaccination records'}, status=status.HTTP_403_FORBIDDEN)

            serializer = VaccinatedSerializer(data=request.data)
            if serializer.is_valid():
                vaccination = serializer.save()
                return Response({
                    'message': 'Vaccination record created successfully',
                    'vaccination': VaccinatedSerializer(vaccination).data
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class VaccinatedDetailView(APIView):

    def get(self, request, vaccination_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            vaccination = Vaccinated.objects.select_related('pet', 'vaccine', 'pet__user').get(id=vaccination_id)

            if not user_service.is_staff() and vaccination.pet.user_id != user_service.user_id:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = VaccinatedSerializer(vaccination)
            return Response(serializer.data)
        except Vaccinated.DoesNotExist:
            return Response({'error': 'Vaccination record not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    def put(self, request, vaccination_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()

            if not user_service.is_staff() and not user_service.is_vet():
                return Response({'error': 'Staff or vet access required to update vaccination records'}, status=status.HTTP_403_FORBIDDEN)

            vaccination = Vaccinated.objects.get(id=vaccination_id)
            serializer = VaccinatedSerializer(vaccination, data=request.data, partial=True)
            
            if serializer.is_valid():
                updated_vaccination = serializer.save()
                return Response({
                    'message': 'Vaccination record updated successfully',
                    'vaccination': VaccinatedSerializer(updated_vaccination).data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Vaccinated.DoesNotExist:
            return Response({'error': 'Vaccination record not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        
class BookAppointmentView(APIView):

    def post(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            request.user_service = user_service
            if user_service.is_client():
                request.data['user'] = user_service.get_user().id
            serializer = BookAppointmentSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                app = serializer.save()

                try:
                    email_service.send_appointment_notification(app)
                except Exception as e:
                    print(f"Failed to send email notifications: {str(e)}")
                
                return Response(BookAppointmentSerializer(app).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

    def put(self, request, appointment_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            request.user_service = user_service
            appointment = Appointment.objects.select_related('user').get(id=appointment_id)
            if user_service.is_client() and appointment.status != 'booked':
                return Response({'error': 'You can\'t edit Appointment when status is confirmed'}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = BookAppointmentSerializer(appointment, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                app = serializer.save()
                return Response(BookAppointmentSerializer(app).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        
class AppointmentView(APIView):
    def get(self, request):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            if user_service.is_staff():
                appointment = Appointment.objects.all().select_related('user')
            elif user_service.is_vet():
                appointment = Appointment.objects.filter(assigned_vet=user_service.get_user()).select_related('user')
            else:
                appointment = Appointment.objects.filter(user=user_service.get_user())
            appointment = appointment.annotate(
                status_order= Case(
                    When(status='booked', then=Value(1)),
                    When(status='confirmed', then=Value(2)),
                    When(status='completed', then=Value(3)),
                    When(status='cancelled', then=Value(4)),
                    When(status='rejected', then=Value(5)),
                    output_field=IntegerField(),
                )
            ).order_by('status_order', 'date')
            serializer = AppointmentListSerializer(appointment, many=True)
            return Response(serializer.data)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        
class AppointmentDetailView(APIView):
    parser_classes = [MultiPartParser, JSONParser]
    # View AppointmentDetail
    def get(self, request, appointment_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            appointment = Appointment.objects.get(id=appointment_id)
            
            if (user_service.is_vet() and (appointment.assigned_vet != user_service.get_user()) or (user_service.is_client() and (appointment.user != user_service.get_user()))):
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            serializer = AppointmentSerializer(appointment)
            pet = Pet.objects.select_related('user').get(id=appointment.pet.id)
            treatment = Treatment.objects.filter(appointment=appointment)
            user = appointment.user
            assgned_vet = appointment.assigned_vet
            vaccinations = Vaccinated.objects.filter(pet=pet).select_related('vaccine').order_by('-date')
            owner_serializer = UserSerializer(user)
            vet_serializer = UserSerializer(assgned_vet)
            pet_serializer = PetSerializer(pet)
            vaccination_serializer = VaccinatedSerializer(vaccinations, many=True)
            treatment_serializer = TreatmentSerializer(treatment, many=True)
            treatment = treatment_serializer.data.copy()
            for i in treatment:
                i['service'] = Service.objects.get(id=i['service']).title
                if i.get('vaccine'):
                    i['vaccine'] = Vaccine.objects.get(id=i['vaccine']).name

            
            response_data = serializer.data.copy()
            # Vet view pet detail & vaccinate
            response_data['pet'] = pet_serializer.data
            response_data['user'] = owner_serializer.data
            response_data['assigned_vet'] = vet_serializer.data if assgned_vet else None
            response_data['vaccinations'] = vaccination_serializer.data
            response_data['total_vaccinations'] = len(vaccination_serializer.data)
            response_data['treatments'] = treatment_serializer.data
            response_data['total_treatments'] = len(treatment_serializer.data)
            # Client view Treatment 
            return Response(response_data)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class UpdateStatusAppointmentView(APIView):
    def put(self, request, appointment_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()

            appointment = Appointment.objects.select_related('user').get(id=appointment_id)
            serializer = UpdateStatusSerializer(appointment, data=request.data, partial=True, context={'user_service': user_service})

            if serializer.is_valid():
                app = serializer.save()
                email_service.send_appointment_status_update(app, appointment.status)
                return Response(UpdateStatusSerializer(app).data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class TreatmentView(APIView):
    parser_classes = [MultiPartParser, JSONParser]
    def get(self, request, appointment_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            
            appointment = Appointment.objects.get(id=appointment_id)
            queryset = Treatment.objects.select_related('appointment').filter(appointment=appointment).order_by('-id')
            serializer = TreatmentSerializer(queryset, many=True)
            
            return Response(serializer.data)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class UpdateTreatmentView(APIView):
    parser_classes = [MultiPartParser, JSONParser]

    def post(self, request, appointment_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()
            appointment = Appointment.objects.get(id=appointment_id)
            if not user_service.is_vet():
                return Response({'error': 'Vet access required to update treatment records'}, status=status.HTTP_403_FORBIDDEN)
            if appointment.assigned_vet != user_service.get_user():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            if appointment.status != 'confirmed':
                return Response({'error': 'Can\'t add treatment to appointment that not confirmed'}, status=status.HTTP_403_FORBIDDEN)
            serializer = UpdateTreatmentSerializer(data=request.data, context={'appointment_id': appointment.id})
            if serializer.is_valid():
                
                treatments = serializer.save()
                return Response({
                    'message': 'Treatment record(s) created successfully',
                    'treatments': TreatmentSerializer(treatments['created_treatments'], many=True).data
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment record not found'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class UserHistoryView(APIView):
    def get(self, request, user_id):
        try:
            user_service = get_user_service(request)
            user_service.check_authentication()

            if not user_service.is_staff():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            treatments = Treatment.objects.filter(appointment__user_id=user_id).select_related('appointment', 'service', 'vaccine', 'appointment__pet').order_by('-id')
            
            treatment_serializer = UserHistorySerializer(treatments, many=True)
            return Response({
                'treatments': treatment_serializer.data
            }, status=status.HTTP_200_OK)
        except Treatment.DoesNotExist:
            return Response({'error': 'Treatment not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)