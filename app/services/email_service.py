import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


class EmailService:

    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 465

    @staticmethod
    def _send_email(to_email: str, subject: str, text: str, html: str):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = os.getenv("EMAIL_FROM")
        msg["To"] = to_email

        msg.set_content(text)
        msg.add_alternative(html, subtype="html")

        with smtplib.SMTP_SSL(
            EmailService.SMTP_HOST,
            EmailService.SMTP_PORT
        ) as smtp:
            smtp.login(
                os.getenv("EMAIL_FROM"),
                os.getenv("EMAIL_PASSWORD")
            )
            smtp.send_message(msg)

    # ---------------- OTP EMAIL ----------------
    @staticmethod
    def send_otp(email: str, otp: str):
        EmailService._send_email(
            to_email=email,
            subject="Your Hackmates Verification Code",
            text=f"""
Hackmates Email Verification

Your OTP is: {otp}

This OTP is valid for 5 minutes.
Do not share this code with anyone.
""",
            html=f"""
<html>
  <body style="margin:0; padding:0; background-color:#f4f6fb;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center" style="padding:40px 0;">
          <table width="100%" style="max-width:420px; background:#ffffff; border-radius:10px; padding:30px; font-family:Arial, sans-serif;">

            <tr>
              <td align="center">
                <h2 style="color:#4F46E5; margin-bottom:10px;">
                  Hackmates Verification
                </h2>
                <p style="color:#555; font-size:14px;">
                  Use the OTP below to verify your email
                </p>
              </td>
            </tr>

            <tr>
              <td align="center" style="padding:20px 0;">
                <div style="
                  font-size:32px;
                  letter-spacing:6px;
                  font-weight:bold;
                  color:#111;
                  background:#f0f2ff;
                  padding:15px 25px;
                  border-radius:8px;
                  display:inline-block;">
                  {otp}
                </div>
              </td>
            </tr>

            <tr>
              <td align="center">
                <p style="font-size:13px; color:#666;">
                  This OTP is valid for <b>5 minutes</b>.
                </p>
                <p style="font-size:12px; color:#999;">
                  If you didn’t request this, you can safely ignore this email.
                </p>
              </td>
            </tr>

            <tr>
              <td align="center" style="padding-top:25px; font-size:12px; color:#aaa;">
                — Hackmates Team
              </td>
            </tr>

          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
        )

    # ---------------- PASSWORD RESET EMAIL ----------------
    @staticmethod
    def send_password_reset(email: str, reset_link: str):
        EmailService._send_email(
            to_email=email,
            subject="Reset Your Hackmates Password",
            text=f"""
Hackmates Password Reset

Click the link below to reset your password:

{reset_link}

This link is valid for 15 minutes.
If you didn’t request this, you can ignore this email.
""",
            html=f"""
<html>
  <body style="margin:0; padding:0; background-color:#f4f6fb;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center" style="padding:40px 0;">
          <table width="100%" style="max-width:420px; background:#ffffff; border-radius:10px; padding:30px; font-family:Arial, sans-serif;">

            <tr>
              <td align="center">
                <h2 style="color:#4F46E5; margin-bottom:10px;">
                  Reset Your Password
                </h2>
                <p style="color:#555; font-size:14px;">
                  Click the button below to reset your Hackmates password
                </p>
              </td>
            </tr>

            <tr>
              <td align="center" style="padding:25px 0;">
                <a href="{reset_link}"
                   style="
                   background:#4F46E5;
                   color:#ffffff;
                   text-decoration:none;
                   padding:14px 24px;
                   border-radius:6px;
                   font-size:14px;
                   font-weight:bold;
                   display:inline-block;">
                  Reset Password
                </a>
              </td>
            </tr>

            <tr>
              <td align="center">
                <p style="font-size:13px; color:#666;">
                  This link is valid for <b>15 minutes</b>.
                </p>
                <p style="font-size:12px; color:#999;">
                  If you didn’t request this, you can safely ignore this email.
                </p>
              </td>
            </tr>

            <tr>
              <td align="center" style="padding-top:25px; font-size:12px; color:#aaa;">
                — Hackmates Team
              </td>
            </tr>

          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
        )
