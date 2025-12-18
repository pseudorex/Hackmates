import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


def send_verification_email(email_to: str, otp: str):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Your Hackmates Verification Code"
        msg["From"] = os.getenv("EMAIL_FROM")
        msg["To"] = email_to

        # Plain text fallback
        msg.set_content(
            f"""
Hackmates Email Verification

Your OTP is: {otp}

This OTP is valid for 5 minutes.
Do not share this code with anyone.

If you didn’t request this, you can safely ignore this email.
"""
        )

        # HTML version
        msg.add_alternative(
            f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2>Hackmates Email Verification</h2>
                <p>Your OTP is:</p>
                <h1>{otp}</h1>
                <p>This OTP is valid for <b>5 minutes</b>.</p>
                <p>If you didn’t request this, you can ignore this email.</p>
              </body>
            </html>
            """,
            subtype="html"
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(os.getenv("EMAIL_FROM"), os.getenv("EMAIL_PASSWORD"))
            smtp.send_message(msg)

        print(f"OTP email sent to {email_to}")

    except Exception as e:
        print(f"Error sending OTP email: {e}")
        raise


def send_password_reset_email(email_to: str, reset_link: str):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Reset Your Hackmates Password"
        msg["From"] = os.getenv("EMAIL_FROM")
        msg["To"] = email_to

        # Plain text
        msg.set_content(
            f"""
Hackmates Password Reset

Click the link below to reset your password:

{reset_link}

This link is valid for 15 minutes.
If you didn’t request this, you can ignore this email.
"""
        )

        # Simple HTML (no CSS)
        msg.add_alternative(
            f"""
            <html>
              <body>
                <h2>Reset Your Hackmates Password</h2>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_link}">Reset Password</a></p>
                <p>This link is valid for <b>15 minutes</b>.</p>
                <p>If you did not request this, please ignore this email.</p>
                <p>— Hackmates Team</p>
              </body>
            </html>
            """,
            subtype="html"
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(os.getenv("EMAIL_FROM"), os.getenv("EMAIL_PASSWORD"))
            smtp.send_message(msg)

        print(f"Password reset email sent to {email_to}")

    except Exception as e:
        print(f"Error sending reset password email: {e}")
        raise
