from django.urls import path
from . import views

urlpatterns = [
    # User management
    path('users/', views.UserView.as_view(), name='user_list'),
    path('users/<str:role>/', views.UserViewByRole.as_view(), name='user_list_by_role'),
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
    path('services/', views.ServiceView.as_view(), name='service_create'),
    path('services/<int:service_id>/', views.UpdateServiceView.as_view(), name='service_manage'),

    # Appointment
    path('appointments/', views.AppointmentView.as_view(), name='appointment'),
    path('appointments/book/', views.BookAppointmentView.as_view(), name='book_appointment'),
    path('appointments/<int:appointment_id>/', views.AppointmentDetailView.as_view(), name='view_appointment'),

    path('appointments/updatestatus/<int:appointment_id>/', views.UpdateStatusAppointmentView.as_view(), name='updatestatus_appointment'),
    path('appointments/edit/<int:appointment_id>/', views.BookAppointmentView.as_view(), name='edit_appointment'),

    path('appointments/treatment/<int:appointment_id>/', views.UpdateTreatmentView.as_view(), name='treatment_appointment'),

    # Treatment history
    path('treatments/<int:user_id>/', views.UserHistoryView.as_view(), name='treatment_list')
]