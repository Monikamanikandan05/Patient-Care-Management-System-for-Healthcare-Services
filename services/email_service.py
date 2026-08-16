import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def _build_html_email(doctor_name: str, doctor_email: str, password: str) -> str:
    portal_url = "http://localhost:8501"
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:30px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">

          <!-- Header -->
          <tr>
            <td align="center" style="background:linear-gradient(135deg,#0d9488,#0891b2);padding:32px 40px;">
              <div style="font-size:28px;font-weight:800;color:#ffffff;letter-spacing:2px;">IPCMS</div>
              <div style="font-size:13px;color:#ccfbf1;margin-top:6px;">Patient Care Management System For Healthcare Services</div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px 40px 24px;">
              <p style="margin:0 0 16px;font-size:15px;color:#1f2937;">Dear Dr. {doctor_name},</p>
              <p style="margin:0 0 24px;font-size:14px;color:#4b5563;line-height:1.6;">
                An administrator has created a Doctor account for you on Patient Care
                Management System For Healthcare Services. Your login credentials are below.
              </p>

              <!-- Credentials Table -->
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                <tr>
                  <td style="padding:12px 0;border-bottom:1px solid #e5e7eb;font-size:13px;color:#6b7280;width:40%;">Name</td>
                  <td style="padding:12px 0;border-bottom:1px solid #e5e7eb;font-size:13px;color:#111827;font-weight:700;">Dr. {doctor_name}</td>
                </tr>
                <tr>
                  <td style="padding:12px 0;border-bottom:1px solid #e5e7eb;font-size:13px;color:#6b7280;">Email</td>
                  <td style="padding:12px 0;border-bottom:1px solid #e5e7eb;font-size:13px;color:#0891b2;">{doctor_email}</td>
                </tr>
                <tr>
                  <td style="padding:12px 0;border-bottom:1px solid #e5e7eb;font-size:13px;color:#6b7280;">Temporary Password</td>
                  <td style="padding:12px 0;border-bottom:1px solid #e5e7eb;font-size:13px;color:#111827;font-weight:700;letter-spacing:1px;">{password}</td>
                </tr>
                <tr>
                  <td style="padding:12px 0;font-size:13px;color:#6b7280;">Portal URL</td>
                  <td style="padding:12px 0;font-size:13px;"><a href="{portal_url}" style="color:#0891b2;">{portal_url}</a></td>
                </tr>
              </table>

              <!-- Security Notice -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0 0;background:#fefce8;border:1px solid #fde68a;border-radius:6px;">
                <tr>
                  <td style="padding:16px 18px;font-size:13px;color:#374151;line-height:1.6;">
                    <strong>Security notice:</strong> You will be required to set a new password the first time
                    you log in. Do not share this temporary password with anyone. If you did not
                    expect this account, contact your hospital administrator immediately.
                  </td>
                </tr>
              </table>

              <p style="margin:24px 0 0;font-size:13px;color:#4b5563;line-height:1.6;">
                This account and its contents are confidential and intended solely for the named recipient.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td align="center" style="padding:16px 40px 28px;border-top:1px solid #f3f4f6;">
              <p style="margin:0;font-size:12px;color:#9ca3af;">
                This is an automated message from Patient Care Management System For Healthcare Services. Please do not reply to this email.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

def send_doctor_credentials_email(doctor_name: str, doctor_email: str, password: str):
    """
    Sends an HTML email to the newly created doctor with their credentials.
    If SMTP variables are not set in the environment, it falls back to logging the email.
    """
    # Always reload .env so latest credentials are picked up without restarting
    load_dotenv(override=True)

    smtp_server   = os.getenv("SMTP_SERVER")
    smtp_port     = os.getenv("SMTP_PORT", 587)
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    subject   = "Welcome to IPCMS – Your Doctor Portal Credentials"
    html_body = _build_html_email(doctor_name, doctor_email, password)

    plain_body = (
        f"Dear Dr. {doctor_name},\n\n"
        f"Your IPCMS Doctor account has been created.\n\n"
        f"Email: {doctor_email}\n"
        f"Temporary Password: {password}\n"
        f"Portal: http://localhost:8501\n\n"
        f"Please change your password on first login.\n\n"
        f"IPCMS Admin Team"
    )

    if smtp_server and smtp_username and smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"]    = f"IPCMS SmartCare <{smtp_username}>"
            msg["To"]      = doctor_email
            msg["Subject"] = subject

            msg.attach(MIMEText(plain_body, "plain"))
            msg.attach(MIMEText(html_body,  "html"))

            server = smtplib.SMTP(smtp_server, int(smtp_port))
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Credentials email sent successfully to {doctor_email}")
            return "sent"
        except Exception as e:
            logger.error(f"Failed to send email to {doctor_email}: {str(e)}")
            print(f"[EMAIL ERROR] {type(e).__name__}: {str(e)}")
            return "failed"
    else:
        logger.warning(f"SMTP not configured. Skipping actual email delivery to {doctor_email}.")
        print("===== EMAIL MOCK =====")
        print(f"To: {doctor_email}")
        print(f"Subject: {subject}")
        print(plain_body)
        print("======================")
        return "mocked"
