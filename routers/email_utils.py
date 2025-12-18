import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


def send_verification_email(email_to: str, otp: str):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Your Hackmates Verification Code'
        msg['From'] = os.getenv("EMAIL_FROM")
        msg['To'] = email_to

        # Plain-text fallback (important for email clients)
        msg.set_content(
            f"""
Hackmates Email Verification

Your OTP is: {otp}

This OTP is valid for 5 minutes.
Do not share this code with anyone.

If you didn’t request this, you can safely ignore this email.
"""
        )

        # HTML version (styled)
        msg.add_alternative(
            f"""
            <html>
              <body style="font-family: Arial, sans-serif; background-color: #f6f8fa; padding: 20px;">
                <div style="max-width: 500px; margin: auto; background: #ffffff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">

                  <h2 style="color: #111827; text-align: center;">
                    Hackmates Email Verification
                  </h2>

                  <p style="color: #374151; font-size: 15px;">
                    Hi 👋,
                  </p>

                  <p style="color: #374151; font-size: 15px;">
                    Use the OTP below to verify your email address:
                  </p>

                  <div style="text-align: center; margin: 24px 0;">
                    <span style="
                      display: inline-block;
                      font-size: 28px;
                      font-weight: bold;
                      letter-spacing: 4px;
                      color: #2563eb;
                      padding: 12px 24px;
                      border: 2px dashed #2563eb;
                      border-radius: 6px;
                    ">
                      {otp}
                    </span>
                  </div>

                  <p style="color: #374151; font-size: 14px;">
                    ⏳ <b>This OTP is valid for 5 minutes.</b>
                  </p>

                  <p style="color: #6b7280; font-size: 13px;">
                    Please do not share this code with anyone for security reasons.
                  </p>

                  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />

                  <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                    If you didn’t request this verification, you can safely ignore this email.
                  </p>

                  <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                    © Hackmates
                  </p>
                </div>
              </body>
            </html>
            """,
            subtype="html"
        )

        # Send email via Gmail SMTP
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
        msg['Subject'] = 'Reset Your Hackmates Password'
        msg['From'] = os.getenv("EMAIL_FROM")
        msg['To'] = email_to

        # Plain text fallback
        msg.set_content(
            f"""
Hackmates Password Reset

Click the link below to reset your password:

{reset_link}

This link is valid for 15 minutes.
If you didn’t request this, you can ignore this email.
"""
        )

        # Simple HTML (NO CSS as you asked)
        msg.add_alternative(
            f"""
            <html>
              <body>
                <h2>Reset Your Hackmates Password</h2>

                <p>Click the link below to reset your password:</p>

                <p>
                  <a href="{reset_link}">
                    Reset Password
                  </a>
                </p>

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



