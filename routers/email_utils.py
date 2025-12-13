import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os
import uuid
from redis_client import redis_client

load_dotenv()

def send_verification_email(email_to: str):
    try:
        # 🔐 Generate ONE-TIME verification token
        verification_token = str(uuid.uuid4())

        # Store in Redis (valid for 24 hours)
        redis_client.set(
            f"email_verify:{verification_token}",
            email_to,
            ex=24 * 60 * 60
        )

        # Verification link (ngrok for now)
        verification_link = (
            "https://uncookable-annelle-combatable.ngrok-free.dev"
            f"/auth/verify-email?token={verification_token}"
        )

        msg = EmailMessage()
        msg["Subject"] = "Verify Your Email - Hackmates"
        msg["From"] = os.getenv("EMAIL_FROM")
        msg["To"] = email_to
        msg.set_content(
            f"""Hi!

Click the link below to verify your email address:

{verification_link}

This link will expire in 24 hours.
If you didn’t request this, you can ignore this email.
"""
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(os.getenv("EMAIL_FROM"), os.getenv("EMAIL_PASSWORD"))
            smtp.send_message(msg)

        print(f"Verification email sent to {email_to}")

    except Exception as e:
        print(f"Error sending verification email: {e}")
        raise
