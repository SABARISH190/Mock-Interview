from flask import render_template, current_app
from flask_mail import Message
from app import mail
from threading import Thread

def send_async_email(app, msg):
    """Helper function to send emails asynchronously."""
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body, attachments=None, sync=False):
    """Send an email.
    
    Args:
        subject (str): Email subject
        sender (str): Sender email address
        recipients (list): List of recipient email addresses
        text_body (str): Plain text email body
        html_body (str): HTML email body
        attachments (list, optional): List of attachments. Defaults to None.
        sync (bool, optional): Whether to send the email synchronously. Defaults to False.
    """
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    # Add attachments if any
    if attachments:
        for attachment in attachments:
            with current_app.open_resource(attachment['file']) as fp:
                msg.attach(
                    filename=attachment['filename'],
                    content_type=attachment['content_type'],
                    data=fp.read(),
                    disposition=attachment.get('disposition', 'attachment')
                )
    
    # Send email asynchronously by default
    if sync:
        mail.send(msg)
    else:
        Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_verification_email(user):
    """Send an email with OTP for email verification."""
    from datetime import datetime
    
    subject = "Verify Your Email Address"
    # Ensure sender is in the format "Name <email@example.com>"
    sender = f"Mock Interview Platform <{current_app.config['MAIL_USERNAME']}>"
    recipients = [user.email]
    
    # Get current datetime for the email template
    now = datetime.utcnow()
    
    # Render email templates with the current datetime
    text_body = render_template('email/verify_email.txt', user=user, now=now)
    html_body = render_template('email/verify_email.html', user=user, now=now)
    
    send_email(subject, sender, recipients, text_body, html_body)

def send_reset_email(user):
    """Send an email with a password reset link."""
    token = user.get_reset_token()
    subject = "Password Reset Request"
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [user.email]
    
    # Render email templates
    text_body = render_template('email/reset_password.txt', user=user, token=token)
    html_body = render_template('email/reset_password.html', user=user, token=token)
    
    send_email(subject, sender, recipients, text_body, html_body)

def send_welcome_email(user):
    """Send a welcome email to new users."""
    subject = "Welcome to Mock Interview Platform"
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [user.email]
    
    # Render email templates
    text_body = render_template('email/welcome.txt', user=user)
    html_body = render_template('email/welcome.html', user=user)
    
    send_email(subject, sender, recipients, text_body, html_body)

def send_interview_scheduled_email(user, interview):
    """Send an email when an interview is scheduled."""
    subject = f"Your {interview.domain} Mock Interview is Scheduled"
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [user.email]
    
    # Render email templates
    text_body = render_template('email/interview_scheduled.txt', user=user, interview=interview)
    html_body = render_template('email/interview_scheduled.html', user=user, interview=interview)
    
    send_email(subject, sender, recipients, text_body, html_body)

def send_interview_completed_email(user, interview, analysis):
    """Send an email when an interview is completed with analysis results."""
    subject = f"Your {interview.domain} Mock Interview Analysis is Ready"
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [user.email]
    
    # Render email templates
    text_body = render_template('email/interview_completed.txt', user=user, interview=interview, analysis=analysis)
    html_body = render_template('email/interview_completed.html', user=user, interview=interview, analysis=analysis)
    
    # Attach the analysis report if available
    attachments = None
    if analysis.report_path:
        attachments = [{
            'file': analysis.report_path,
            'filename': f"interview_analysis_{interview.id}.pdf",
            'content_type': 'application/pdf'
        }]
    
    send_email(subject, sender, recipients, text_body, html_body, attachments=attachments)
