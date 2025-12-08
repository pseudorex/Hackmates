import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def send_verification_email(email_to: str, token: str):
    try:
        # Your verification link (adjust domain later for production)
        verification_link = f"http://localhost:8000/auth/verify-email?token={token}"

        # Create the email
        msg = EmailMessage()
        msg['Subject'] = 'Verify Your Email - Hackmates'
        msg['From'] = os.getenv("EMAIL_FROM")
        msg['To'] = email_to
        msg.set_content(
            f"Hi!\n\nClick the link below to verify your email address:\n\n{verification_link}\n\n"
            "If you didn’t request this, you can ignore this message."
        )

        # Connect securely via Gmail SMTP (SSL)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(os.getenv("EMAIL_FROM"), os.getenv("EMAIL_PASSWORD"))
            smtp.send_message(msg)

        print(f"Verification email sent to {email_to}")

    except Exception as e:
        print(f"Error sending email: {e}")
        raise
