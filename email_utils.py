"""
Email utility functions for sending verification and password reset emails.
"""
from flask import url_for, render_template
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from config import Config

def init_mail(app, mail):
    """Initialize email configuration"""
    app.config.from_object(Config)
    mail.init_app(app)
    return mail

def generate_token(email, salt=None):
    """Generate a secure token for email verification or password reset"""
    serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
    if salt is None:
        salt = Config.SECURITY_PASSWORD_SALT
    return serializer.dumps(email, salt=salt)

def confirm_token(token, expiration=3600, salt=None):
    """
    Confirm a token and return the email if valid.
    expiration: time in seconds (default 1 hour)
    """
    serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
    if salt is None:
        salt = Config.SECURITY_PASSWORD_SALT
    try:
        email = serializer.loads(
            token,
            salt=salt,
            max_age=expiration
        )
        return email
    except Exception:
        return False

def send_verification_email(mail, user_email, token):
    """Send email verification link to user"""
    try:
        from flask import current_app
        verify_url = url_for('verify_email', token=token, _external=True)
        
        msg = Message(
            'Verify Your Email - Task & Budget Manager',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user_email]
        )
        
        msg.html = render_template('emails/verify_email.html', 
                                   verify_url=verify_url,
                                   email=user_email)
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_password_reset_email(mail, user_email, token):
    """Send password reset link to user"""
    try:
        from flask import current_app
        reset_url = url_for('reset_password', token=token, _external=True)
        
        msg = Message(
            'Reset Your Password - Task & Budget Manager',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user_email]
        )
        
        msg.html = render_template('emails/reset_password.html',
                                   reset_url=reset_url,
                                   email=user_email)
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        import traceback
        traceback.print_exc()
        return False
