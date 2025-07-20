"""
Email utility functions for the recipe recommendation system.

This module provides email sending functionality for password reset and other notifications.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import logging

# Set up logging
logger = logging.getLogger(__name__)

def send_email(to_email, subject, html_body, text_body=None):
    """
    Send an email using SMTP configuration.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        html_body (str): HTML email body
        text_body (str, optional): Plain text email body
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get email configuration from Flask app config
        mail_server = current_app.config.get('MAIL_SERVER')
        mail_port = current_app.config.get('MAIL_PORT')
        mail_use_tls = current_app.config.get('MAIL_USE_TLS')
        mail_use_ssl = current_app.config.get('MAIL_USE_SSL')
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        mail_default_sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        
        # Check if email is configured
        if not all([mail_server, mail_username, mail_password]):
            logger.warning("Email configuration is incomplete. Cannot send email.")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = mail_default_sender
        msg['To'] = to_email
        
        # Add text part if provided
        if text_body:
            text_part = MIMEText(text_body, 'plain')
            msg.attach(text_part)
        
        # Add HTML part
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Create SMTP connection
        if mail_use_ssl:
            server = smtplib.SMTP_SSL(mail_server, mail_port)
        else:
            server = smtplib.SMTP(mail_server, mail_port)
            if mail_use_tls:
                server.starttls()
        
        # Login and send email
        server.login(mail_username, mail_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_password_reset_email(to_email, reset_token, user_name=None):
    """
    Send a password reset email with a secure reset link.
    
    Args:
        to_email (str): Recipient email address
        reset_token (str): Password reset token
        user_name (str, optional): User's name for personalization
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Create reset link
    # In production, this should use your actual domain
    reset_link = f"http://localhost:5000/reset-password?token={reset_token}"
    
    # Email subject
    subject = "Reset Your Sisa Rasa Password"
    
    # Personalized greeting
    greeting = f"Hi {user_name}," if user_name else "Hi,"
    
    # HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Password</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .container {{
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 24px;
                font-weight: bold;
                color: #e1cc7f;
                margin-bottom: 10px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: #e1cc7f;
                color: #0b0a0a;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .button:hover {{
                background-color: #f9e59a;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                font-size: 12px;
                color: #666;
                text-align: center;
            }}
            .warning {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">Sisa Rasa</div>
                <h2>Password Reset Request</h2>
            </div>
            
            <p>{greeting}</p>
            
            <p>We received a request to reset your password for your Sisa Rasa account. If you made this request, click the button below to reset your password:</p>
            
            <div style="text-align: center;">
                <a href="{reset_link}" class="button">Reset My Password</a>
            </div>
            
            <div class="warning">
                <strong>Important:</strong> This link will expire in 1 hour for security reasons. If you don't reset your password within this time, you'll need to request a new reset link.
            </div>
            
            <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
            
            <p>If you're having trouble clicking the button, copy and paste the following link into your web browser:</p>
            <p style="word-break: break-all; color: #666; font-size: 14px;">{reset_link}</p>
            
            <div class="footer">
                <p>This email was sent by Sisa Rasa - Recipe Recommendation System</p>
                <p>If you have any questions, please contact our support team.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    {greeting}
    
    We received a request to reset your password for your Sisa Rasa account.
    
    To reset your password, please click on the following link:
    {reset_link}
    
    This link will expire in 1 hour for security reasons.
    
    If you didn't request a password reset, you can safely ignore this email.
    
    Best regards,
    The Sisa Rasa Team
    """
    
    return send_email(to_email, subject, html_body, text_body)

def is_email_configured():
    """
    Check if email configuration is properly set up.
    
    Returns:
        bool: True if email is configured, False otherwise
    """
    try:
        mail_server = current_app.config.get('MAIL_SERVER')
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        
        return all([mail_server, mail_username, mail_password])
    except:
        return False
