import argparse
import time
from db import init_db, save_application, get_application
from workflow import run_workflow
from scheduler import start_scheduler, scheduler

def run_borderline_flow():
    """
    Creates a 'BORDERLINE' application and demonstrates the workflow pausing
    for manager review, triggering the reminder scheduler.
    """
    print("--- Running BORDERLINE Case ---")
    start_scheduler()

    # Create a sample application that will result in 'BORDERLINE'
    # Income: 65k, Loan: 300k -> Borderline
    app_id = save_application(name="Ram", income=65000, loan_amount=300000, email="ram@example.com")
    print(f"Created application #{app_id}")

    app_data = get_application(app_id)

    print("\n--- Running workflow ---")
    final_status = "UNKNOWN"
    for message in run_workflow(app_data):
        print(message)
        if "**Final Status:**" in message:
            final_status = message.split("**Final Status:**")[1].strip()

    if final_status == 'PENDING_MANAGER':
        print("\nWorkflow paused, waiting for manager review.")
        print("The scheduler will now send reminders every day (as configured).")
        print("To simulate manager approval, run the Streamlit app and approve it.")
        print("Keeping script alive for 10 seconds to show scheduler is running...")
        time.sleep(10)
        print("Scheduler is running in the background. Exiting main script.")
        scheduler.shutdown(wait=False) # Allows background thread to finish
    else:
        print(f"\nWorkflow finished with status: {final_status}")

def run_automated_high_risk_flow():
    """
    Creates a 'HIGH_RISK' application and runs it through the fully automated
    workflow, including simulated document submission and review.
    """
    print("--- Running HIGH_RISK Automated Case ---")
    # Create a sample application that will be marked as 'HIGH_RISK'
    # Income: 70k, Loan: 500k -> High risk
    app_id = save_application(name="Divya", income=70000, loan_amount=500000, email="divya@example.com")
    print(f"Created Application #{app_id} for Automated Flow")

    app_data = get_application(app_id)

    # Run the workflow and print each step's output
    for message in run_workflow(app_data):
        print(message)
    print("\nWorkflow finished.")

if __name__ == "__main__":
    # Initialize the database once
    init_db()

    parser = argparse.ArgumentParser(
        description="Run a demonstration of the loan approval workflow.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "flow",
        nargs="?",
        choices=["borderline", "automated"],
        default="automated",
        help=(
            "Which flow to run:\n"
            "  'automated'  - (Default) Demonstrates the fully automated HIGH_RISK path.\n"
            "  'borderline' - Demonstrates the BORDERLINE path where the workflow pauses for a manager."
        )
    )
    args = parser.parse_args()

    if args.flow == "borderline":
        run_borderline_flow()
    else: # "automated"
        run_automated_high_risk_flow()
