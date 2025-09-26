from minio import Minio
from minio.error import S3Error
from django.conf import settings
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
    
    def is_authenticated(self):
        return self.user_id is not None
    
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
        if not self.is_authenticated():
            raise PermissionError("Authentication required")

def get_user_service(request):
    return UserService(request.session)

minio_service = MinIOService()