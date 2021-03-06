"""
Django settings for dailyfresh project.

Generated by 'django-admin startproject' using Django 3.2.13.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os.path
from pathlib import Path
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
import django.core.mail.backends.smtp
import django_redis

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ozjdf)wz*)-r7g+y1e=0j=67%2+cedasga0h4oqql!4=exdu&p'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tinymce',
    'haystack',
    'user',
    'shopping_cart',
    'goods',
    'orders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dailyfresh.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dailyfresh.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dailyfresh',
        'HOST': '127.0.0.1',
        'PORT': 3306,
        'USER': 'root',
        'PASSWORD': '123456'
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# ?????????????????????????????????
STATIC_ROOT = '/var/www/dailyfresh/static'

# ??????????????????????????????
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.AllowAllUsersModelBackend']

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# tinymce?????????
TINYMCE_DEFAULT_CONFIG = {
    'theme': 'advanced',
    'width': 600,
    'height': 400,
}

# ????????????django????????????????????????
AUTH_USER_MODEL = 'user.User'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'tianhao_2022@163.com'
EMAIL_HOST_PASSWORD = ''
EMAIL_FROM = '????????????<tianhao_2022@163.com>'

# EMAIL_USE_SSL = True
# EMAIL_USE_TLS = False

# ??????session??????????????????
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ??????????????????redis
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/3",    # DB??????3
        # "TIMEOUT": None,   # ?????????????????????300???
        'TIMEOUT': 300,
        "OPTIONS": {
            'MAX_ENTRIES': 300,    # ??????????????????
            'CULL_FREQUENCY': 3,    # ?????????????????????1/3
            # "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # "PASSWORD":"xxxxxx" # ??????????????????
        }
    }
}

# django???????????? ????????????????????????????????????????????????
LOGIN_URL = '/user/login'
# ??????????????????????????????????????????
DEFAULT_FILE_STORAGE = 'utils.fdfs.storage.FDFSStorage'
# ???????????????Storage??????client_conf??????
DEFAULT_FDFS_CLIENT_CONF = './utils/fdfs/client.conf'
# ???????????????Storage??????url??????
DEFAULT_FDFS_BASE_URL = 'http://192.168.47.131:8888/'

# ???????????????????????????
HAYSTACK_CONNECTIONS = {
    'default': {
        # ??????whoosh??????
        'ENGINE': 'haystack.backends.whoosh_cn_backend.WhooshEngine',
        # ??????????????????
        'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
    }
}

# ?????????????????????????????????????????????????????????
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
# ????????????????????????????????????????????????20
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 1
