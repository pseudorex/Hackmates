from .jwt_utils import create_email_verification_token
from routers.email_utils import send_verification_email

class EmailService:
    @staticmethod
    def send_verification(user):
        token = create_email_verification_token(user.email)
        send_verification_email(user.email, token)
