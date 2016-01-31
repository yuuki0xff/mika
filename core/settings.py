"""
Django settings for mika project.
"""

import os
import sys

APPLICATION_NAME='Mika'
PROTOCOLS = ['shinGETsu/0.7', 'Mikaduki/0.1']
VERSION = '0.3.0'

MESSAGE_QUEUE_SOCK_FILE = "/run/mika/msgq.sock"
MAX_THREADS = 16
MAX_CONNECTIONS = 16
HTTP_TIMEOUT = 16
MAX_NODES = 10

RECENT_INTERVAL=30*60
PING_INTERVAL=5*60
JOIN_INTERVAL=5*60

NODE_NAME = 'test'
# NODE_NAME = '<IP_ADDRESS>:<PORT>+server_api'
# example:
#   '192.0.2.2:80+server_api'
assert(NODE_NAME)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '$#7@64zk2+aqqmg3fsd3$9ucs4&!2#t-pvlwp4$j270h_x&x+*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['*']


# Set the module search path
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([
	_ROOT_DIR,
	_ROOT_DIR+'/require'])


# Application definition

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app.shingetsu',
    'lib.msgqueued',
    'app.rest_api',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'lib.middleware.SQLAlchemySessionMiddleware',
)

ROOT_URLCONF = 'core.urls'

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

# For SQLAlchemy
if all((x in os.environ) for x in ['MIKA_DB_TYPE', 'MIKA_DB_AUTH', 'MIKA_DB_ADDR', 'MIKA_DB_NAME',]):
	DB_ADDRESS = '{}://{}@{}/{}?{}'.format(
			os.environ['MIKA_DB_TYPE'],
			os.environ['MIKA_DB_AUTH'],
			os.environ['MIKA_DB_ADDR'],
			os.environ['MIKA_DB_NAME'],
			os.environ['MIKA_DB_OPT'],
			)
else:
	with open(_ROOT_DIR+'/core/db.address') as _fp:
		DB_ADDRESS=_fp.read()

# For Django
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db.sqlite3' #os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
# *** DON'T EDIT THESE VARIABLES ***

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%Y/%m/%d %H:%M:%S"
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'logging.NullHandler',
        },
        'console': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'standard',
        },
        'logfile':{
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'standard',
            'filename': '/srv/log/mika.log'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['logfile'],
            'level': 'WARNING',
            'propagate': True,
        },
        'app': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'lib': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

