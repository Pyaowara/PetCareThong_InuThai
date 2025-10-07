# scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.utils import timezone
from datetime import timedelta
from .models import Appointment
from .services import email_service

def send_appointment_reminders():
    try:
        target_date = timezone.now().date() + timedelta(days=2)
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

    except Exception as e:
        print(f"Error in reminder job: {str(e)}")

def delete_old_job_executions(max_age=604_800):
    DjangoJobExecution.objects.delete_old_job_executions(max_age)

def start():
    from django_apscheduler.jobstores import DjangoJobStore

    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    if scheduler.running:
        print("Scheduler is already running. Exiting start function.")
        return
    scheduler.add_job(
        send_appointment_reminders,
        trigger='cron',
        hour=9,
        minute=0,
        id='send_appointment_reminders',
        max_instances=1,
        replace_existing=True,
    )
    print("✅ Added job 'send_appointment_reminders' to run daily at 9:00 AM")

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
        print(" Starting scheduler...")
        scheduler.start()
    except KeyboardInterrupt:
        print("Stopping scheduler...")
        scheduler.shutdown()
        print("Scheduler shut down successfully!")
    except Exception as e:
        print(f" Error starting scheduler: {e}")
