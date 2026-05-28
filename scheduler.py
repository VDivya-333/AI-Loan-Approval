import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from db import get_application
from utils import send_email

load_dotenv()

scheduler = BackgroundScheduler(daemon=True)

def _manager_followup_job(app_id: str):
    """
    Job that sends a reminder for a specific application.
    If the application is no longer pending, it removes itself from the schedule.
    """
    print(f"\n[Scheduler] Running follow-up job for Application #{app_id}...")
    app = get_application(app_id)

    if not app or app.get("status") != "PENDING_MANAGER":
        print(f"[Scheduler] Application #{app_id} no longer pending. Removing follow-up job.")
        scheduler.remove_job(f"manager_followup_{app_id}", misfire_grace_time=None)
    else:
        manager_email = os.getenv("MANAGER_EMAIL", "manager@example.com")
        send_email(
            to=manager_email,
            subject=f"Reminder: Approval Needed for Application #{app['id']}",
            body=f"Dear Manager,\n\nThe loan application for {app['name']} is still pending your approval.\n"
                 f"Loan Amount: {app['loan_amount']}\nIncome: {app['income']}\n\n"
                 "Please review as soon as possible.\n",
        )
        print(f"[Scheduler] Reminder email sent for Application #{app['id']}")

def start_manager_followups(app_id: str):
    """Schedules a recurring follow-up job for a specific application."""
    job_id = f"manager_followup_{app_id}"
    print(f"[Scheduler] Scheduling daily follow-ups for Application #{app_id} with job ID: {job_id}")
    scheduler.add_job(
        _manager_followup_job, "interval", days=1, id=job_id, args=[app_id]
    )

def start_scheduler():
    """Starts the main scheduler process."""
    scheduler.start()
    print("Scheduler started... Ready to schedule and run jobs.")