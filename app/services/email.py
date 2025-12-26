import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings


async def send_email(to_email: str, subject: str, body_html: str, body_text: str = None):
    """Send an email via Gmail SMTP."""
    settings = get_settings()
    
    if not settings.smtp_user or not settings.smtp_password:
        print(f"SMTP not configured. Would send email to {to_email}: {subject}")
        return False
    
    message = MIMEMultipart("alternative")
    message["From"] = f"{settings.site_name} <{settings.smtp_from}>"
    message["To"] = to_email
    message["Subject"] = subject
    
    if body_text:
        message.attach(MIMEText(body_text, "plain"))
    message.attach(MIMEText(body_html, "html"))
    
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


async def send_contact_notification(name: str, email: str, subject: str, message: str):
    """Notify admin of new contact form submission."""
    settings = get_settings()
    
    html = f"""
    <h2>New Contact Form Submission</h2>
    <p><strong>From:</strong> {name} ({email})</p>
    <p><strong>Subject:</strong> {subject}</p>
    <hr>
    <p>{message.replace(chr(10), '<br>')}</p>
    """
    
    await send_email(
        to_email=settings.smtp_from,
        subject=f"[Contact] {subject}",
        body_html=html,
        body_text=f"From: {name} ({email})\n\n{message}"
    )


async def send_contact_confirmation(to_email: str, name: str):
    """Send confirmation to the person who submitted contact form."""
    settings = get_settings()
    
    html = f"""
    <p>Hi {name},</p>
    <p>Thanks for reaching out! I've received your message and will get back to you soon.</p>
    <p>Best,<br>{settings.site_name}</p>
    """
    
    await send_email(
        to_email=to_email,
        subject="Thanks for reaching out!",
        body_html=html,
        body_text=f"Hi {name},\n\nThanks for reaching out! I've received your message and will get back to you soon.\n\nBest,\n{settings.site_name}"
    )
