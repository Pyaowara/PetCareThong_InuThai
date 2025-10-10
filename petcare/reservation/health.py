from django.http import JsonResponse
from django.views import View
from django.db import connection
import os

class HealthCheckView(View):
    def get(self, request):
        """
        Health check endpoint for production monitoring
        """
        try:
            # Check database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Check environment
            debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
            
            return JsonResponse({
                'status': 'healthy',
                'database': 'connected',
                'debug': debug_mode,
                'environment': 'production' if not debug_mode else 'development'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'unhealthy',
                'error': str(e)
            }, status=503)