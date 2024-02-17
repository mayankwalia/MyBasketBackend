# -------------- IMPORTING MODULES --------------- #
import os
import application.utils.loadenv
from datetime import timedelta

# -------------- PATH OF BASE DIRECTORY --------------- #
basedir = os.path.abspath(os.path.dirname(__file__)) # path of the base directory

# -------------- CONFIGURATION CLASSES --------------- #
class Config(object):
    """
    Base class for some common configurations of the MyBasket App.
    """

    DEBUG = False
    SQLITE_DB_DIR = None
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECURITY_TOKEN_AUTHENTICATION_HEADER = "Authentication-Token"
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
    CELERY_SEND_EVENTS = True
    CELERY_TRACK_STARTED = True

class LocalDevelopmentConfig(Config):
    """
    Class for some common configurations of the Flask App related to Local Development.
    """

    ##### Flask APP Config #####
    DEBUG = True

    ##### Database Config #####
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    
    SECRET_KEY = os.getenv('SECRET_KEY') # Used for token generation
    SECURITY_PASSWORD_SALT = "thisissaltt"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    ##### Flask JWT Config #####
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=12)

    ##### Celery Config #####
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/1'
    ENABLE_UTC = False
    broker_connection_retry_on_startup=True
    TIMEZONE = "Asia/kolkata"

    ##### Flask Mail Config #####
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    
    UPLOAD_FOLDER= 'application/static/images/'
    
    # Redis Cache
    CACHE_TYPE = "RedisCache"
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = "mybasket_cache"
    CACHE_REDIS_URL = "redis://localhost:6379"
    CACHE_REDIS_HOST = "localhost"
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_PASSWORD = ""  