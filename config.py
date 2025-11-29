import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'  # Change for production
    # Build an absolute path to the instance DB to avoid sqlite file-open issues on Windows.
    basedir = os.path.abspath(os.path.dirname(__file__))
    _default_db_path = os.path.join(basedir, 'instance', 'app.db')
    # Ensure forward slashes in the URI to be compatible with SQLAlchemy file URI parsing on Windows
    _default_db_uri = 'sqlite:///' + _default_db_path.replace('\\', '/')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or _default_db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False