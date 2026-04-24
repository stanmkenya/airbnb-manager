"""
Email service for sending user invitations and notifications.

Supports multiple email providers:
- SendGrid (recommended for production)
- AWS SES
- SMTP (Gmail, etc.)

To use:
1. Choose your email provider
2. Set environment variables (see .env.example)
3. Uncomment the appropriate send_email function
"""

import os
from typing import Optional


def send_invitation_email_sendgrid(
    to_email: str,
    user_name: str,
    reset_link: str,
    invited_by: str = "Your Admin"
) -> bool:
    """
    Send invitation email using SendGrid.

    Setup:
    1. Install: pip install sendgrid
    2. Set environment variable: SENDGRID_API_KEY
    3. Set environment variable: SENDGRID_FROM_EMAIL
    """
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        api_key = os.getenv('SENDGRID_API_KEY')
        from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@yourdomain.com')

        if not api_key:
            raise ValueError("SENDGRID_API_KEY not set in environment variables")

        # Create email content
        subject = "You've been invited to Airbnb Property Manager"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Airbnb Property Manager!</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>

                    <p>{invited_by} has invited you to join the Airbnb Property Manager platform.</p>

                    <p>To get started, please set your password by clicking the button below:</p>

                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Set Your Password</a>
                    </p>

                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #e5e7eb; padding: 10px; border-radius: 3px;">
                        {reset_link}
                    </p>

                    <p><strong>Important:</strong> This link will expire in 1 hour for security reasons.</p>

                    <p>After setting your password, you can sign in at: <a href="https://yourdomain.com">https://yourdomain.com</a></p>

                    <p>If you didn't expect this invitation, you can safely ignore this email.</p>

                    <p>Best regards,<br>The Airbnb Property Manager Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Create message
        message = Mail(
            from_email=Email(from_email),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )

        # Send email
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)

        print(f"[EMAIL] Invitation sent to {to_email} via SendGrid (status: {response.status_code})")
        return True

    except Exception as e:
        print(f"[EMAIL] Error sending invitation via SendGrid: {e}")
        return False


def send_invitation_email_ses(
    to_email: str,
    user_name: str,
    reset_link: str,
    invited_by: str = "Your Admin"
) -> bool:
    """
    Send invitation email using AWS SES.

    Setup:
    1. Install: pip install boto3
    2. Configure AWS credentials (aws configure)
    3. Verify your email/domain in AWS SES
    4. Set environment variable: AWS_SES_FROM_EMAIL
    """
    try:
        import boto3
        from botocore.exceptions import ClientError

        from_email = os.getenv('AWS_SES_FROM_EMAIL', 'noreply@yourdomain.com')
        aws_region = os.getenv('AWS_REGION', 'us-east-1')

        # Create SES client
        client = boto3.client('ses', region_name=aws_region)

        subject = "You've been invited to Airbnb Property Manager"

        html_body = f"""
        <html>
        <body>
            <h2>Welcome to Airbnb Property Manager!</h2>
            <p>Hi {user_name},</p>
            <p>{invited_by} has invited you to join the platform.</p>
            <p>Click the link below to set your password:</p>
            <p><a href="{reset_link}">Set Your Password</a></p>
            <p>This link expires in 1 hour.</p>
        </body>
        </html>
        """

        # Send email
        response = client.send_email(
            Source=from_email,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': html_body}}
            }
        )

        print(f"[EMAIL] Invitation sent to {to_email} via AWS SES (MessageId: {response['MessageId']})")
        return True

    except ClientError as e:
        print(f"[EMAIL] AWS SES error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"[EMAIL] Error sending invitation via AWS SES: {e}")
        return False


def send_invitation_email_smtp(
    to_email: str,
    user_name: str,
    reset_link: str,
    invited_by: str = "Your Admin"
) -> bool:
    """
    Send invitation email using SMTP (e.g., Gmail).

    Setup:
    1. Set environment variables:
       - SMTP_SERVER (e.g., smtp.gmail.com)
       - SMTP_PORT (e.g., 587)
       - SMTP_USERNAME (your email)
       - SMTP_PASSWORD (app password for Gmail)
       - SMTP_FROM_EMAIL

    For Gmail: https://support.google.com/accounts/answer/185833
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('SMTP_FROM_EMAIL', smtp_username)

        if not smtp_username or not smtp_password:
            raise ValueError("SMTP credentials not set in environment variables")

        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = "You've been invited to Airbnb Property Manager"
        message['From'] = from_email
        message['To'] = to_email

        html_content = f"""
        <html>
        <body>
            <h2>Welcome to Airbnb Property Manager!</h2>
            <p>Hi {user_name},</p>
            <p>{invited_by} has invited you to join the platform.</p>
            <p>Click the link below to set your password:</p>
            <p><a href="{reset_link}">Set Your Password</a></p>
            <p>Or copy this link: {reset_link}</p>
            <p>This link expires in 1 hour.</p>
        </body>
        </html>
        """

        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)

        print(f"[EMAIL] Invitation sent to {to_email} via SMTP")
        return True

    except Exception as e:
        print(f"[EMAIL] Error sending invitation via SMTP: {e}")
        return False


# Main function to use - switch based on your email provider
def send_invitation_email(
    to_email: str,
    user_name: str,
    reset_link: str,
    invited_by: str = "Your Admin"
) -> bool:
    """
    Send invitation email using configured email service.

    Set EMAIL_PROVIDER environment variable to choose:
    - 'sendgrid' (recommended)
    - 'ses' (AWS SES)
    - 'smtp' (Gmail, etc.)
    """
    provider = os.getenv('EMAIL_PROVIDER', 'none')

    if provider == 'sendgrid':
        return send_invitation_email_sendgrid(to_email, user_name, reset_link, invited_by)
    elif provider == 'ses':
        return send_invitation_email_ses(to_email, user_name, reset_link, invited_by)
    elif provider == 'smtp':
        return send_invitation_email_smtp(to_email, user_name, reset_link, invited_by)
    else:
        print(f"[EMAIL] No email provider configured. Set EMAIL_PROVIDER environment variable.")
        print(f"[EMAIL] Password reset link for {to_email}: {reset_link}")
        return False
