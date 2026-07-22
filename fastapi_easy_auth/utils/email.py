import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi_easy_auth.config import AuthConfig

def send_otp_email_sync(config: AuthConfig, to_email: str, code: str, context_message: str = "your verification code"):
    """
    Send an OTP email synchronously via SMTP.
    Typically you would call this in a background task (e.g. asyncio.to_thread).
    """
    if not all([config.smtp_host, config.smtp_port, config.smtp_user, config.smtp_password, config.from_email]):
        print(f"⚠️ SMTP not fully configured. Simulating email to {to_email} with code: {code}")
        return

    msg = MIMEMultipart()
    msg['From'] = config.from_email
    msg['To'] = to_email
    msg['Subject'] = "Verification Code"
    
    body = f"Hello,\n\nHere is {context_message}:\n\n{code}\n\nThis code will expire in {config.otp_expire_minutes} minutes.\n\nThanks,\nSupport Team"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(config.smtp_host, config.smtp_port)
        server.starttls()
        server.login(config.smtp_user, config.smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"📧 Successfully sent OTP via SMTP to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send SMTP email to {to_email}: {e}")
