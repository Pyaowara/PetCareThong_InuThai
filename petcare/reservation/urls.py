from django.urls import path
from . import views

urlpatterns = [
    # User management
    path('users/', views.UserView.as_view(), name='user_list_create'),
    path('users/<int:user_id>/', views.UserDetailView.as_view(), name='user_detail'),
    
    # Authentication
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user_profile'),
]