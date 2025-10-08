from minio import Minio
from minio.error import S3Error
from django.conf import settings
from django.core.mail import send_mail
from datetime import timedelta
import io

class MinIOService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    def upload_image(self, file_obj, file_name, content_type='image/jpeg'):
        try:
            file_obj.seek(0)
            file_data = file_obj.read()
            file_size = len(file_data)
            file_stream = io.BytesIO(file_data)

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                data=file_stream,
                length=file_size,
                content_type=content_type
            )
            
            return True
        except S3Error as e:
            print(f"Error uploading file: {e}")
            return False

    def get_image_url(self, file_name, expires_days=7):
        try:
            expires = timedelta(days=expires_days)
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                expires=expires
            )
            return url
        except S3Error as e:
            print(f"Error getting image URL: {e}")
            return None
    
    def delete_image(self, file_name):
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=file_name
            )
            return True
        except S3Error as e:
            print(f"Error deleting file: {e}")
            return False
        
class UserService:
    def __init__(self, session):
        self.session = session
        self.user_id = session.get('user_id', None)

    def get_user(self):
        from .models import User
        if self.user_id:
            try:
                return User.objects.get(id=self.user_id)
            except User.DoesNotExist:
                return None
        return None

    def get_role(self):
        user = self.get_user()
        return user.role if user else None

    def has_role(self, required_role):
        user_role = self.get_role()
        return user_role == required_role if user_role else False

    def is_staff(self):
        return self.has_role('staff')

    def is_client(self):
        return self.has_role('client')

    def is_vet(self):
        return self.has_role('vet')

    def check_authentication(self):
        if not self.user_id:
            raise PermissionError("Authentication required")

def get_user_service(request):
    return UserService(request.session)

class EmailService:
    @staticmethod
    def send_appointment_notification(appointment):
        try:
            from .models import User
            staff_users = User.objects.filter(role='staff', active=True)

            context = {
                'appointment': appointment,
                'pet': appointment.pet,
                'user': appointment.user,
                'appointment_date': appointment.date.strftime('%B %d, %Y at %I:%M %p'),
                'status_display': appointment.get_status_display(),
            }

            EmailService._send_user_appointment_email(appointment.user, context)
            for staff in staff_users:
                EmailService._send_staff_appointment_email(staff, context)
                
        except Exception as e:
            print(f"Error in sending appointment notifications: {str(e)}")
    
    @staticmethod
    def send_appointment_status_update(appointment, old_status=None):
        try:
            context = {
                'appointment': appointment,
                'pet': appointment.pet,
                'user': appointment.user,
                'appointment_date': appointment.date.strftime('%B %d, %Y at %I:%M %p'),
                'status_display': appointment.get_status_display(),
                'old_status': old_status,
            }

            if appointment.status == 'confirmed' and appointment.assigned_vet:
                EmailService._send_vet_assignment_email(appointment.assigned_vet, context)
                EmailService._send_user_confirmation_email(appointment.user, context)

            elif appointment.status == 'cancelled' and old_status != 'cancelled':
                EmailService._send_user_cancellation_email(appointment.user, context)
                from .models import User
                staff_users = User.objects.filter(role='staff', active=True)
                for staff in staff_users:
                    EmailService._send_staff_cancellation_email(staff, context)

            elif appointment.status == 'rejected':
                EmailService._send_user_rejection_email(appointment.user, context)
                
        except Exception as e:
            print(f"Error in sending status update notifications: {str(e)}")
    
    @staticmethod
    def _send_vet_assignment_email(vet, context):
        try:
            subject = f"Appointment Assigned - {context['pet'].name} ({context['user'].full_name})"
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #b8860b; border-bottom: 2px solid #b8860b; padding-bottom: 10px;">
                        👨‍⚕️ Appointment Assignment
                    </h2>
                    
                    <p>Dear Dr. {vet.full_name},</p>
                    
                    <p>You have been assigned to an appointment that has been confirmed:</p>
                    
                    <div style="background: #f8f6f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #b8860b; margin-top: 0;">Appointment Details</h3>
                        {f'<div style="text-align: center; margin-bottom: 15px;"><img src="{context["pet"].get_image_url()}" alt="{context["pet"].name}" style="max-width: 150px; max-height: 150px; border-radius: 8px; object-fit: cover; border: 2px solid #b8860b;"><br><small style="color: #666; font-style: italic;">{context["pet"].name}</small></div>' if context['pet'].get_image_url() else ''}
                        <p><strong>Pet Owner:</strong> {context['user'].full_name}</p>
                        <p><strong>Contact:</strong> {context['user'].email} {f"| {context['user'].phone_number}" if context['user'].phone_number else ""}</p>
                        <p><strong>Pet Name:</strong> {context['pet'].name}</p>
                        <p><strong>Pet Breed:</strong> {context['pet'].breed}</p>
                        <p><strong>Pet Gender:</strong> {context['pet'].gender}</p>
                        <p><strong>Date & Time:</strong> {context['appointment_date']}</p>
                        <p><strong>Purpose:</strong> {context['appointment'].purpose}</p>
                        <p><strong>Status:</strong> <span style="color: #28a745; font-weight: bold;">CONFIRMED</span></p>
                        {f"<p><strong>Remarks:</strong> {context['appointment'].remarks}</p>" if context['appointment'].remarks else ""}
                    </div>
                    
                    <div style="background: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Next Steps:</strong></p>
                        <p style="margin: 5px 0 0 0;">Please prepare for this appointment and update the status to "Completed" after the visit.</p>
                    </div>
                    
                    <p>Thank you for your commitment to providing excellent pet care.</p>
                    
                    <p>Best regards,<br>
                    <strong>PetCare System</strong></p>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            Appointment Assignment
            
            Dear Dr. {vet.full_name},
            
            You have been assigned to an appointment that has been confirmed:
            
            Appointment Details:
            - Pet Owner: {context['user'].full_name}
            - Contact: {context['user'].email} {f"| {context['user'].phone_number}" if context['user'].phone_number else ""}
            - Pet Name: {context['pet'].name}
            - Pet Breed: {context['pet'].breed}
            - Pet Gender: {context['pet'].gender}
            - Date & Time: {context['appointment_date']}
            - Purpose: {context['appointment'].purpose}
            - Status: CONFIRMED
            {f"- Remarks: {context['appointment'].remarks}" if context['appointment'].remarks else ""}
            
            Next Steps:
            Please prepare for this appointment and update the status to "Completed" after the visit.
            
            Best regards,
            PetCare System
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[vet.email],
                html_message=html_message,
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"Failed to send vet assignment email: {str(e)}")
    
    @staticmethod
    def _send_user_confirmation_email(user, context):
        try:
            subject = f"Appointment Confirmed - {context['pet'].name}"
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #b8860b; border-bottom: 2px solid #b8860b; padding-bottom: 10px;">
                        ✅ Appointment Confirmed
                    </h2>
                    
                    <p>Dear {user.full_name},</p>
                    
                    <p>Great news! Your appointment has been confirmed by our staff:</p>
                    
                    <div style="background: #f8f6f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #b8860b; margin-top: 0;">Confirmed Appointment Details</h3>
                        {f'<div style="text-align: center; margin-bottom: 15px;"><img src="{context["pet"].get_image_url()}" alt="{context["pet"].name}" style="max-width: 150px; max-height: 150px; border-radius: 8px; object-fit: cover; border: 2px solid #b8860b;"></div>' if context['pet'].get_image_url() else ''}
                        <p><strong>Pet:</strong> {context['pet'].name}</p>
                        <p><strong>Breed:</strong> {context['pet'].breed}</p>
                        <p><strong>Date & Time:</strong> {context['appointment_date']}</p>
                        <p><strong>Purpose:</strong> {context['appointment'].purpose}</p>
                        <p><strong>Assigned Veterinarian:</strong> Dr. {context['appointment'].assigned_vet.full_name if context['appointment'].assigned_vet else 'TBA'}</p>
                        <p><strong>Status:</strong> <span style="color: #28a745; font-weight: bold;">CONFIRMED</span></p>
                        {f"<p><strong>Remarks:</strong> {context['appointment'].remarks}</p>" if context['appointment'].remarks else ""}
                    </div>
                    
                    <div style="background: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Important Reminders:</strong></p>
                        <ul style="margin: 5px 0 0 20px; padding: 0;">
                            <li>Please arrive 10 minutes early</li>
                            <li>Bring any previous medical records</li>
                            <li>If you need to reschedule, please contact us at least 24 hours in advance</li>
                        </ul>
                    </div>
                    
                    <p>We look forward to seeing you and {context['pet'].name}!</p>
                    
                    <p>Best regards,<br>
                    <strong>PetCare Team</strong></p>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            Appointment Confirmed
            
            Dear {user.full_name},
            
            Great news! Your appointment has been confirmed by our staff:
            
            Confirmed Appointment Details:
            - Pet: {context['pet'].name}
            - Breed: {context['pet'].breed}
            - Date & Time: {context['appointment_date']}
            - Purpose: {context['appointment'].purpose}
            - Assigned Veterinarian: Dr. {context['appointment'].assigned_vet.full_name if context['appointment'].assigned_vet else 'TBA'}
            - Status: CONFIRMED
            {f"- Remarks: {context['appointment'].remarks}" if context['appointment'].remarks else ""}
            
            Important Reminders:
            - Please arrive 10 minutes early
            - Bring any previous medical records
            - If you need to reschedule, please contact us at least 24 hours in advance
            
            We look forward to seeing you and {context['pet'].name}!
            
            Best regards,
            PetCare Team
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"Failed to send user confirmation email: {str(e)}")
    
    @staticmethod
    def _send_user_cancellation_email(user, context):
        try:
            subject = f"Appointment Cancelled - {context['pet'].name}"
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc3545; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">
                        ❌ Appointment Cancelled
                    </h2>
                    
                    <p>Dear {user.full_name},</p>
                    
                    <p>Your appointment has been cancelled as requested:</p>
                    
                    <div style="background: #f8f6f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #dc3545; margin-top: 0;">Cancelled Appointment Details</h3>
                        {f'<div style="text-align: center; margin-bottom: 15px;"><img src="{context["pet"].get_image_url()}" alt="{context["pet"].name}" style="max-width: 150px; max-height: 150px; border-radius: 8px; object-fit: cover; border: 2px solid #b8860b;"></div>' if context['pet'].get_image_url() else ''}
                        <p><strong>Pet:</strong> {context['pet'].name}</p>
                        <p><strong>Breed:</strong> {context['pet'].breed}</p>
                        <p><strong>Original Date & Time:</strong> {context['appointment_date']}</p>
                        <p><strong>Purpose:</strong> {context['appointment'].purpose}</p>
                        <p><strong>Status:</strong> <span style="color: #dc3545; font-weight: bold;">CANCELLED</span></p>
                    </div>
                    
                    <div style="background: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Need to Reschedule?</strong></p>
                        <p style="margin: 5px 0 0 0;">If you'd like to book a new appointment, please visit our booking system or contact us directly.</p>
                    </div>
                    
                    <p>Thank you for notifying us. We hope to see you and {context['pet'].name} again soon!</p>
                    
                    <p>Best regards,<br>
                    <strong>PetCare Team</strong></p>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            Appointment Cancelled
            
            Dear {user.full_name},
            
            Your appointment has been cancelled as requested:
            
            Cancelled Appointment Details:
            - Pet: {context['pet'].name}
            - Breed: {context['pet'].breed}
            - Original Date & Time: {context['appointment_date']}
            - Purpose: {context['appointment'].purpose}
            - Status: CANCELLED
            
            Need to Reschedule?
            If you'd like to book a new appointment, please visit our booking system or contact us directly.
            
            Thank you for notifying us. We hope to see you and {context['pet'].name} again soon!
            
            Best regards,
            PetCare Team
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"Failed to send user cancellation email: {str(e)}")
    
    @staticmethod
    def _send_staff_cancellation_email(staff, context):
        try:
            subject = f"Appointment Cancelled - {context['pet'].name} ({context['user'].full_name})"
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc3545; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">
                        🚫 Appointment Cancellation Alert
                    </h2>
                    
                    <p>Dear {staff.full_name},</p>
                    
                    <p>An appointment has been cancelled by the client:</p>
                    
                    <div style="background: #f8f6f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #dc3545; margin-top: 0;">Cancelled Appointment Details</h3>
                        {f'<div style="text-align: center; margin-bottom: 15px;"><img src="{context["pet"].get_image_url()}" alt="{context["pet"].name}" style="max-width: 150px; max-height: 150px; border-radius: 8px; object-fit: cover; border: 2px solid #b8860b;"><br><small style="color: #666; font-style: italic;">{context["pet"].name}</small></div>' if context['pet'].get_image_url() else ''}
                        <p><strong>Pet Owner:</strong> {context['user'].full_name}</p>
                        <p><strong>Contact:</strong> {context['user'].email} {f"| {context['user'].phone_number}" if context['user'].phone_number else ""}</p>
                        <p><strong>Pet Name:</strong> {context['pet'].name}</p>
                        <p><strong>Pet Breed:</strong> {context['pet'].breed}</p>
                        <p><strong>Original Date & Time:</strong> {context['appointment_date']}</p>
                        <p><strong>Purpose:</strong> {context['appointment'].purpose}</p>
                        <p><strong>Status:</strong> <span style="color: #dc3545; font-weight: bold;">CANCELLED</span></p>
                    </div>
                    
                    <div style="background: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Action Required:</strong></p>
                        <p style="margin: 5px 0 0 0;">Please update your schedule and notify the assigned veterinarian if applicable.</p>
                    </div>
                    
                    <p>This appointment slot is now available for other bookings.</p>
                    
                    <p>Best regards,<br>
                    <strong>PetCare System</strong></p>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            Appointment Cancellation Alert
            
            Dear {staff.full_name},
            
            An appointment has been cancelled by the client:
            
            Cancelled Appointment Details:
            - Pet Owner: {context['user'].full_name}
            - Contact: {context['user'].email} {f"| {context['user'].phone_number}" if context['user'].phone_number else ""}
            - Pet Name: {context['pet'].name}
            - Pet Breed: {context['pet'].breed}
            - Original Date & Time: {context['appointment_date']}
            - Purpose: {context['appointment'].purpose}
            - Status: CANCELLED
            
            Action Required:
            Please update your schedule and notify the assigned veterinarian if applicable.
            
            This appointment slot is now available for other bookings.
            
            Best regards,
            PetCare System
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[staff.email],
                html_message=html_message,
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"Failed to send staff cancellation email: {str(e)}")
    
    @staticmethod
    def _send_user_rejection_email(user, context):
        try:
            subject = f"Appointment Request Declined - {context['pet'].name}"
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc3545; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">
                        ⚠️ Appointment Request Declined
                    </h2>
                    
                    <p>Dear {user.full_name},</p>
                    
                    <p>We regret to inform you that your appointment request has been declined:</p>
                    
                    <div style="background: #f8f6f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #dc3545; margin-top: 0;">Declined Appointment Details</h3>
                        {f'<div style="text-align: center; margin-bottom: 15px;"><img src="{context["pet"].get_image_url()}" alt="{context["pet"].name}" style="max-width: 150px; max-height: 150px; border-radius: 8px; object-fit: cover; border: 2px solid #b8860b;"></div>' if context['pet'].get_image_url() else ''}
                        <p><strong>Pet:</strong> {context['pet'].name}</p>
                        <p><strong>Breed:</strong> {context['pet'].breed}</p>
                        <p><strong>Requested Date & Time:</strong> {context['appointment_date']}</p>
                        <p><strong>Purpose:</strong> {context['appointment'].purpose}</p>
                        <p><strong>Status:</strong> <span style="color: #dc3545; font-weight: bold;">DECLINED</span></p>
                        {f"<p><strong>Staff Note:</strong> {context['appointment'].vet_note}</p>" if context['appointment'].vet_note else ""}
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #daa520; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Alternative Options:</strong></p>
                        <ul style="margin: 5px 0 0 20px; padding: 0;">
                            <li>Try booking a different date and time</li>
                            <li>Contact us directly to discuss alternative arrangements</li>
                            <li>Consider our emergency services if this is urgent</li>
                        </ul>
                    </div>
                    
                    <p>We apologize for any inconvenience. Please don't hesitate to contact us if you have any questions or would like to discuss other options.</p>
                    
                    <p>Best regards,<br>
                    <strong>PetCare Team</strong></p>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            Appointment Request Declined
            
            Dear {user.full_name},
            
            We regret to inform you that your appointment request has been declined:
            
            Declined Appointment Details:
            - Pet: {context['pet'].name}
            - Breed: {context['pet'].breed}
            - Requested Date & Time: {context['appointment_date']}
            - Purpose: {context['appointment'].purpose}
            - Status: DECLINED
            {f"- Staff Note: {context['appointment'].vet_note}" if context['appointment'].vet_note else ""}
            
            Alternative Options:
            - Try booking a different date and time
            - Contact us directly to discuss alternative arrangements
            - Consider our emergency services if this is urgent
            
            We apologize for any inconvenience. Please don't hesitate to contact us if you have any questions.
            
            Best regards,
            PetCare Team
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"Failed to send user rejection email: {str(e)}")
    
    @staticmethod
    def _send_user_appointment_email(user, context):
        try:
            subject = f"Appointment Confirmation - {context['pet'].name}"
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #b8860b; border-bottom: 2px solid #b8860b; padding-bottom: 10px;">
                        🐾 Appointment Confirmation
                    </h2>
                    
                    <p>Dear {user.full_name},</p>
                    
                    <p>Your appointment has been successfully booked. Here are the details:</p>
                    
                    <div style="background: #f8f6f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #b8860b; margin-top: 0;">Appointment Details</h3>
                        {f'<div style="text-align: center; margin-bottom: 15px;"><img src="{context["pet"].get_image_url()}" alt="{context["pet"].name}" style="max-width: 150px; max-height: 150px; border-radius: 8px; object-fit: cover; border: 2px solid #b8860b;"></div>' if context['pet'].get_image_url() else ''}
                        <p><strong>Pet:</strong> {context['pet'].name}</p>
                        <p><strong>Breed:</strong> {context['pet'].breed}</p>
                        <p><strong>Date & Time:</strong> {context['appointment_date']}</p>
                        <p><strong>Purpose:</strong> {context['appointment'].purpose}</p>
                        <p><strong>Status:</strong> {context['status_display']}</p>
                        {f"<p><strong>Remarks:</strong> {context['appointment'].remarks}</p>" if context['appointment'].remarks else ""}
                    </div>
                    
                    <div style="background: #fff8e1; padding: 15px; border-left: 4px solid #daa520; margin: 20px 0;">
                        <p style="margin: 0;"><strong>What's Next?</strong></p>
                        <p style="margin: 5px 0 0 0;">Our staff will review your appointment and confirm the details shortly. You'll receive another email once your appointment is confirmed.</p>
                    </div>
                    
                    <p>If you have any questions or need to make changes, please contact us.</p>
                    
                    <p>Best regards,<br>
                    <strong>PetCare Team</strong></p>
                </div>
            </body>
            </html>
            """

            plain_message = f"""
            Appointment Confirmation
            
            Dear {user.full_name},
            
            Your appointment has been successfully booked. Here are the details:
            
            Appointment Details:
            - Pet: {context['pet'].name}
            - Breed: {context['pet'].breed}
            - Date & Time: {context['appointment_date']}
            - Purpose: {context['appointment'].purpose}
            - Status: {context['status_display']}
            {f"- Remarks: {context['appointment'].remarks}" if context['appointment'].remarks else ""}
            
            What's Next?
            Our staff will review your appointment and confirm the details shortly.
            
            Best regards,
            PetCare Team
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"Failed to send user email: {str(e)}")

    @staticmethod
    def _send_staff_appointment_email(staff, context):
        try:
            subject = f"New Appointment - {context['pet'].name} ({context['user'].full_name})"
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #b8860b; border-bottom: 2px solid #b8860b; padding-bottom: 10px;">
                        🏥 New Appointment Alert
                    </h2>
                    
                    <p>Dear {staff.full_name},</p>
                    
                    <p>A new appointment has been booked and requires your attention:</p>
                    
                    <div style="background: #f8f6f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #b8860b; margin-top: 0;">Appointment Details</h3>
                        {f'<div style="text-align: center; margin-bottom: 15px;"><img src="{context["pet"].get_image_url()}" alt="{context["pet"].name}" style="max-width: 150px; max-height: 150px; border-radius: 8px; object-fit: cover; border: 2px solid #b8860b;"><br><small style="color: #666; font-style: italic;">{context["pet"].name}</small></div>' if context['pet'].get_image_url() else ''}
                        <p><strong>Pet Owner:</strong> {context['user'].full_name}</p>
                        <p><strong>Contact:</strong> {context['user'].email} {f"| {context['user'].phone_number}" if context['user'].phone_number else ""}</p>
                        <p><strong>Pet Name:</strong> {context['pet'].name}</p>
                        <p><strong>Pet Breed:</strong> {context['pet'].breed}</p>
                        <p><strong>Pet Gender:</strong> {context['pet'].gender}</p>
                        <p><strong>Date & Time:</strong> {context['appointment_date']}</p>
                        <p><strong>Purpose:</strong> {context['appointment'].purpose}</p>
                        <p><strong>Current Status:</strong> {context['status_display']}</p>
                        {f"<p><strong>Remarks:</strong> {context['appointment'].remarks}</p>" if context['appointment'].remarks else ""}
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #daa520; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Action Required:</strong></p>
                        <p style="margin: 5px 0 0 0;">Please review this appointment and update the status as needed through the admin panel.</p>
                    </div>
                    
                    <p>You can manage this appointment through the PetCare management system.</p>
                    
                    <p>Best regards,<br>
                    <strong>PetCare System</strong></p>
                </div>
            </body>
            </html>
            """

            plain_message = f"""
            New Appointment Alert
            
            Dear {staff.full_name},
            
            A new appointment has been booked and requires your attention:
            
            Appointment Details:
            - Pet Owner: {context['user'].full_name}
            - Contact: {context['user'].email} {f"| {context['user'].phone_number}" if context['user'].phone_number else ""}
            - Pet Name: {context['pet'].name}
            - Pet Breed: {context['pet'].breed}
            - Pet Gender: {context['pet'].gender}
            - Date & Time: {context['appointment_date']}
            - Purpose: {context['appointment'].purpose}
            - Current Status: {context['status_display']}
            {f"- Remarks: {context['appointment'].remarks}" if context['appointment'].remarks else ""}
            
            Action Required:
            Please review this appointment and update the status as needed.
            
            Best regards,
            PetCare System
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[staff.email],
                html_message=html_message,
                fail_silently=False,
            )
            
        except Exception as e:
            print(f"Failed to send staff email: {str(e)}")

    @staticmethod
    def send_appointment_reminder(appointment):
        try:
            subject = f"Appointment Reminder - {appointment.pet.name} Tomorrow!"
            
            context = {
                'appointment': appointment,
                'pet': appointment.pet,
                'user': appointment.user,
                'appointment_date': appointment.date.strftime('%B %d, %Y at %I:%M %p'),
                'days_until': 2
            }
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #b8860b; border-bottom: 2px solid #b8860b; padding-bottom: 10px;">
                        ⏰ Appointment Reminder
                    </h2>
                    
                    <p>Dear {appointment.user.full_name},</p>
                    
                    <p>This is a friendly reminder that you have an upcoming appointment in <strong>2 days</strong>:</p>
                    
                    <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
                        <h3 style="color: #28a745; margin-top: 0;">📅 Upcoming Appointment</h3>
                        {f'<div style="text-align: center; margin-bottom: 15px;"><img src="{appointment.pet.get_image_url()}" alt="{appointment.pet.name}" style="max-width: 150px; max-height: 150px; border-radius: 8px; object-fit: cover; border: 2px solid #b8860b;"></div>' if appointment.pet.get_image_url() else ''}
                        <p><strong>Pet:</strong> {appointment.pet.name}</p>
                        <p><strong>Breed:</strong> {appointment.pet.breed}</p>
                        <p><strong>Date & Time:</strong> {context['appointment_date']}</p>
                        <p><strong>Purpose:</strong> {appointment.purpose}</p>
                        <p><strong>Assigned Veterinarian:</strong> Dr. {appointment.assigned_vet.full_name if appointment.assigned_vet else 'TBA'}</p>
                        <p><strong>Status:</strong> <span style="color: #28a745; font-weight: bold;">CONFIRMED</span></p>
                        {f"<p><strong>Remarks:</strong> {appointment.remarks}</p>" if appointment.remarks else ""}
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #daa520; margin: 20px 0;">
                        <p style="margin: 0;"><strong>📋 Pre-Appointment Checklist:</strong></p>
                        <ul style="margin: 10px 0 0 20px; padding: 0;">
                            <li>Ensure your pet has fasted if required for the procedure</li>
                            <li>Bring any previous medical records or test results</li>
                            <li>Prepare a list of questions for the veterinarian</li>
                            <li>Arrive 10-15 minutes early for check-in</li>
                            <li>Bring your pet's favorite toy or blanket for comfort</li>
                        </ul>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>📞 Need to make changes?</strong></p>
                        <p style="margin: 5px 0 0 0;">If you need to reschedule or cancel, please contact us at least 24 hours in advance to avoid cancellation fees.</p>
                    </div>
                    
                    <p>We look forward to seeing you and {appointment.pet.name} soon!</p>
                    
                    <p>Best regards,<br>
                    <strong>PetCare Team</strong></p>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            Appointment Reminder
            
            Dear {appointment.user.full_name},
            
            This is a friendly reminder that you have an upcoming appointment in 2 days:
            
            Upcoming Appointment:
            - Pet: {appointment.pet.name}
            - Breed: {appointment.pet.breed}
            - Date & Time: {context['appointment_date']}
            - Purpose: {appointment.purpose}
            - Assigned Veterinarian: Dr. {appointment.assigned_vet.full_name if appointment.assigned_vet else 'TBA'}
            - Status: CONFIRMED
            {f"- Remarks: {appointment.remarks}" if appointment.remarks else ""}
            
            Pre-Appointment Checklist:
            - Ensure your pet has fasted if required for the procedure
            - Bring any previous medical records or test results
            - Prepare a list of questions for the veterinarian
            - Arrive 10-15 minutes early for check-in
            - Bring your pet's favorite toy or blanket for comfort
            
            Need to make changes?
            If you need to reschedule or cancel, please contact us at least 24 hours in advance.
            
            We look forward to seeing you and {appointment.pet.name} soon!
            
            Best regards,
            PetCare Team
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            print(f"Reminder email sent for appointment {appointment.id} to {appointment.user.email}")
            
        except Exception as e:
            print(f"Failed to send reminder email for appointment {appointment.id}: {str(e)}")

minio_service = MinIOService()
email_service = EmailService()