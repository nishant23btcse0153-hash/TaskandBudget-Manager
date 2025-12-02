import os
from urllib.parse import quote_plus

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # PostgreSQL configuration
    # Priority: DATABASE_URL (Render) > Individual env vars > Local defaults
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Handle Render.com postgres:// to postgresql:// conversion
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Fallback to individual environment variables (for local development)
        DB_USER = os.environ.get('DB_USER', 'postgres')
        DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Nise@23678')
        DB_HOST = os.environ.get('DB_HOST', 'localhost')
        DB_PORT = os.environ.get('DB_PORT', '5432')
        DB_NAME = os.environ.get('DB_NAME', 'task_expense_db')
        
        # URL-encode the password to handle special characters like @
        _encoded_password = quote_plus(DB_PASSWORD)
        SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{_encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration (Flask-Mail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # Your email
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # App password
    # Format: "Display Name <email@example.com>"
    _mail_username = MAIL_USERNAME
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or (f'Task & Budget Manager <{_mail_username}>' if _mail_username else None)
    
    # Security settings
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'dev-salt-change-in-production'
    
    # Server configuration for url_for with _external=True
    SERVER_NAME = os.environ.get('SERVER_NAME')  # e.g., 'localhost:8000' for dev
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')  # 'https' for production
    
    # Notification scheduler configuration
    NOTIFICATION_CHECK_INTERVAL_HOURS = int(os.environ.get('NOTIFICATION_CHECK_INTERVAL_HOURS', 1))  # Check every 1 hour by default