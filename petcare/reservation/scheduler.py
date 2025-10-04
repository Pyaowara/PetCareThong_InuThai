from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

from .models import Appointment
from .services import email_service

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

def send_appointment_reminders():
    """
    Job function to send reminder emails for appointments 2 days in advance
    This function is called by APScheduler every day at 4:30 PM
    """
    try:
        # Calculate the target date (2 days from now)
        target_date = timezone.now().date() + timedelta(days=2)
        
        # Create a cache key for today's reminder run
        cache_key = f"reminder_sent_{target_date.strftime('%Y%m%d')}"
        
        # Check if we've already sent reminders for this date today
        if cache.get(cache_key):
            print(f"Reminders for {target_date} already sent today. Skipping.")
            return
        
        # Find confirmed appointments for the target date
        appointments = Appointment.objects.filter(
            status='confirmed',
            date__date=target_date
        ).select_related('user', 'pet', 'assigned_vet')
        
        sent_count = 0
        error_count = 0
        
        print(f"[{timezone.now()}] Starting appointment reminder job...")
        print(f"Looking for confirmed appointments on {target_date}")

        if not appointments.exists():
            print(f"No confirmed appointments found for {target_date}")
            # Still mark as run to prevent multiple checks
            cache.set(cache_key, True, 60*60*24)  # Cache for 24 hours
            return
        
        print(f"Found {appointments.count()} confirmed appointments")
        
        for appointment in appointments:
            try:
                email_service.send_appointment_reminder(appointment)
                sent_count += 1
                print(f"✅ Sent reminder to {appointment.user.email} for appointment {appointment.id} ({appointment.pet.name})")
            except Exception as e:
                error_count += 1
                print(f"❌ Failed to send reminder for appointment {appointment.id}: {str(e)}")
        
        print(f"Reminder job completed: {sent_count} sent, {error_count} failed")
        
        # Mark reminders as sent for this date
        cache.set(cache_key, True, 60*60*24)  # Cache for 24 hours
        
    except Exception as e:
        print(f"Error in reminder job: {str(e)}")

def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries older than `max_age` from the database.
    It helps to prevent the database from filling up with old historical records that are no
    longer useful.
    
    :param max_age: The maximum length of time to retain historical job execution records.
                    Defaults to 7 days.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)

def start():
    """
    Start the scheduler and add jobs
    """
    if scheduler.running:
        return
    
    # Add the appointment reminder job to run daily at 4:37 PM
    scheduler.add_job(
        send_appointment_reminders,
        trigger='cron',
        hour=16,
        minute=37,
        id='send_appointment_reminders',
        max_instances=1,
        replace_existing=True,
    )
    print("Added job 'send_appointment_reminders' to run daily at 4:37 PM")

    # Add job to clean up old job execution records
    scheduler.add_job(
        delete_old_job_executions,
        trigger="interval",
        days=1,
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True,
    )
    print("Added daily job: 'delete_old_job_executions'.")

    try:
        print("Starting scheduler...")
        scheduler.start()
    except KeyboardInterrupt:
        print("Stopping scheduler...")
        scheduler.shutdown()
        print("Scheduler shut down successfully!")