"""
Django settings for pisces project.

Generated by 'django-admin startproject' using Django 2.0.10.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""
import os

from . import config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config.DJANGO_SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config.DJANGO_DEBUG

ALLOWED_HOSTS = config.DJANGO_ALLOWED_HOSTS

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'health_check',
    'fetcher',
    'merger',
    'transformer',
    'silk',
    'django_cron',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'silk.middleware.SilkyMiddleware',
]

ROOT_URLCONF = 'pisces.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'transformer', 'templates')],
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

WSGI_APPLICATION = 'pisces.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": config.SQL_ENGINE,
        "NAME": config.SQL_DATABASE,
        "USER": config.SQL_USER,
        "PASSWORD": config.SQL_PASSWORD,
        "HOST": config.SQL_HOST,
        "PORT": config.SQL_PORT,
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = "fetcher.User"

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = config.DJANGO_STATIC_ROOT

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25
}

# Silk Profiling
SILKY_PYTHON_PROFILER = config.SILKY_PYTHON_PROFILER

# Django cron settings
CRON_CLASSES = [
    "fetcher.cron.DeletedArchivesSpaceArchivalObjects",
    "fetcher.cron.DeletedArchivesSpaceFamilies",
    "fetcher.cron.DeletedArchivesSpaceOrganizations",
    "fetcher.cron.DeletedArchivesSpacePeople",
    "fetcher.cron.DeletedArchivesSpaceResources",
    "fetcher.cron.DeletedArchivesSpaceSubjects",
    "fetcher.cron.DeletedCartographerArrangementMapComponents",
    "fetcher.cron.UpdatedArchivesSpaceArchivalObjects",
    "fetcher.cron.UpdatedArchivesSpaceFamilies",
    "fetcher.cron.UpdatedArchivesSpaceOrganizations",
    "fetcher.cron.UpdatedArchivesSpacePeople",
    "fetcher.cron.UpdatedArchivesSpaceResources",
    "fetcher.cron.UpdatedArchivesSpaceSubjects",
    "fetcher.cron.UpdatedCartographerArrangementMapComponents",
]
DJANGO_CRON_LOCK_BACKEND = "django_cron.backends.lock.cache.CacheLock"

ARCHIVESSPACE = {
    "baseurl": config.AS_BASEURL,
    "username": config.AS_USERNAME,
    "password": config.AS_PASSWORD,
    "repo": config.AS_REPO_ID,
}

CARTOGRAPHER = {
    "baseurl": config.CARTOGRAPHER_BASEURL,
    "health_check_path": config.CARTOGRAPHER_HEALTH_CHECK_PATH,
}

INDEX_DELETE_URL = config.INDEX_DELETE_URL
