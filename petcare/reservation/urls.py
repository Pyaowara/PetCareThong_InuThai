from django.urls import path
from . import views

urlpatterns = [
    # User management
    path('users/', views.UserView.as_view(), name='user_list'),
    path('users/<int:user_id>/', views.UserDetailView.as_view(), name='user_detail'),
    
    # Pet management
    path('pets/', views.PetView.as_view(), name='pet_list_create'),
    path('pets/<int:pet_id>/', views.PetDetailView.as_view(), name='pet_detail'),
    
    # Vaccine management
    path('vaccines/', views.VaccineView.as_view(), name='vaccine_list_create'),
    path('vaccines/<int:vaccine_id>/', views.VaccineDetailView.as_view(), name='vaccine_detail'),
    
    # Vaccination records management
    path('vaccinations/', views.VaccinatedView.as_view(), name='vaccination_list_create'),
    path('vaccinations/<int:vaccination_id>/', views.VaccinatedDetailView.as_view(), name='vaccination_detail'),
    
    # Authentication
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user_profile'),

    #Service
    path('service/', views.ServiceView.as_view(), name='service_create'),
    path('service/<int:service_id>/', views.UpdateServiceView.as_view(), name='service_manage'),

    # Appointment
    path('appointment/', views.AppointmentView.as_view(), name='appointment'),
    path('appointment/book/', views.BookAppointmentView.as_view(), name='book_appointment'),
    path('appointment/<int:appointment_id>/', views.AppointmentDetailView.as_view(), name='view_appointment'),
    path('appointment/update/<int:appointment_id>/', views.UpdateAppointmentView.as_view(), name='update_appointment'),

]