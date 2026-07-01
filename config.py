import os

basedir = os.path.abspath(os.path.dirname(__file__))

class config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key')

    FLASK_APP = 'flasky.py'

    # Google OAuth - User Authentication
    GOOGLE_CLIENT_ID = os.getenv('FLASK_GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('FLASK_GOOGLE_CLIENT_SECRET')
    OAUTH_REDIRECT_URI = os.getenv('FLASK_OAUTH_REDIRECT_URI')

    # Gmail OAuth - Email Sending
    GMAIL_SERVICE_ACCOUNT_EMAIL = os.getenv('GMAIL_SERVICE_ACCOUNT_EMAIL')
    GMAIL_PRIVATE_KEY = os.getenv('GMAIL_PRIVATE_KEY')
    GMAIL_SENDER_EMAIL = os.getenv('GMAIL_SENDER_EMAIL')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FLASKY_POSTS_PER_PAGE = 20
    FLASKY_FOLLOWERS_PER_PAGE = 50
    FLASKY_COMMENTS_PER_PAGE = 30
    FLASKY_SLOW_DB_QUERY_TIME = 0.5
    
    SSL_REDIRECT = False

    SQLALCHEMY_RECORD_QUERIES = True
    FLASKY_SLOW_DB_QUERY_TIME = 0.1
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

class ProductionConfig(config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

class TestingConfig(config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'

config = {
    'development':DevelopmentConfig,
    'production':ProductionConfig,
    'testing': TestingConfig,
    'default':ProductionConfig
}

