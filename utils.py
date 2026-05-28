
import os
import smtplib
from email.mime.text import MIMEText

def send_email(to: str, subject: str, body: str):
    """
    Sends an email.
    If the environment variable EMAIL_MODE is set to 'console', it prints the email
    to the console instead of sending it. Otherwise, it uses SMTP to send a real email.
    """
    email_mode = os.getenv("EMAIL_MODE", "smtp") # Default to 'smtp'

    if email_mode == "console":
        print("\n--- CONSOLE EMAIL ---")
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print("Body:")
        print(body)
        print("---------------------\n")
        return

    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    if not sender_email or not sender_password:
        print(f"[Email ERROR] EMAIL_USER and EMAIL_PASS environment variables must be set to send emails.")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"[Email] Sent to {to} | Subject: {subject}")
    except Exception as e:
        print(f"[Email ERROR] {e}")
