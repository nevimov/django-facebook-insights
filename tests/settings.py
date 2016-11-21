import os

try:
    FACEBOOK_INSIGHTS_ACCESS_TOKEN = os.environ['FACEBOOK_INSIGHTS_ACCESS_TOKEN']
except KeyError:
    from tests.secret import FACEBOOK_INSIGHTS_ACCESS_TOKEN

FACEBOOK_INSIGHTS_API_VERSION = '2.3'

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True

SECRET_KEY = 'dummy-key'

USE_TZ = True  # Prevents some ValueError's with SQLite backend

INSTALLED_APPS = [
    'facebook_insights',
    'tests',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'facebook_insights': {
            'handlers': ['console'],
            'level': os.getenv('FBI_LOG_LEVEL', 'ERROR'),
        },
    },
}
