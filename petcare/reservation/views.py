from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import *
from .serializers import *
from .services import get_user_service

class UserView(APIView):
    parser_classes = [MultiPartParser, JSONParser]
    
    def get(self, request):
        try:
            user_service = get_user_service(request)
            if user_service.is_authenticated():
                if not user_service.is_staff():
                    return Response({'error': 'Staff access required'}, status=status.HTTP_403_FORBIDDEN)

            users = User.objects.all()
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
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
            print(user)
            request.session['user_id'] = user.id
            
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        request.session.flush()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

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
            if user_service.is_authenticated():
                if not user_service.is_staff():
                    return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Not Authenticated'}, status=status.HTTP_403_FORBIDDEN)

            services = Service.objects.all()
            serializer = ServiceSerializer(services, many=True)
            return Response(serializer.data)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Create Service
    def post(self, request):
        try:
            user_service = get_user_service(request)
            if user_service.is_authenticated():
                if not user_service.is_staff():
                    return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Not Authenticated'}, status=status.HTTP_403_FORBIDDEN)
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
            if user_service.is_authenticated():
                if not user_service.is_staff():
                    return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Not Authenticated'}, status=status.HTTP_403_FORBIDDEN)

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
    def post(self, request, service_id):
        try:
            user_service = get_user_service(request)
            if user_service.is_authenticated():
                if not user_service.is_staff():
                    return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Not Authenticated'}, status=status.HTTP_403_FORBIDDEN)
            
            service = Service.objects.get(id=service_id)
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
            if user_service.is_authenticated():
                if not user_service.is_staff():
                    return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Not Authenticated'}, status=status.HTTP_403_FORBIDDEN)
            
            service = Service.objects.get(id=service_id)
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
