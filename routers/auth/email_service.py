from routers.email_utils import (
    send_verification_email,
    send_password_reset_email
)

class EmailService:
    @staticmethod
    def send_otp(email: str, otp: str):
        send_verification_email(email, otp)

    @staticmethod
    def send_password_reset(email: str, reset_link: str):
        print("Sending password reset email to:", email)
        send_password_reset_email(email, reset_link)
