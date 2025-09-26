from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import User
from .serializers import UserSerializer, LoginSerializer, UserProfileSerializer

class UserView(APIView):
    parser_classes = [MultiPartParser, JSONParser]
    
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
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
            user = User.objects.get(id=user_id)
            serializer = UserSerializer(user)

            delete_info = serializer.delete(user)
            response_message = f'User {delete_info["user_email"]} deleted successfully'
                
            return Response({
                'message': response_message,
                'deleted_user_id': delete_info['user_id'],
                'image_deleted': delete_info['image_deleted']
            }, status=status.HTTP_200_OK)
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
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = User.objects.get(id=user_id)
            serializer = UserProfileSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)