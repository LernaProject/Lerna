"""
Django settings for lerna project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

import contextlib

from .base_settings import *


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# Must be overridden in local_settings.py

SECRET_KEY = ""

DEBUG = False


# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ajax_select",
    "scripts",
    "core",
    "users",
    "news",
    "contests",
    "dbtrash",
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
)

ROOT_URLCONF = "lerna.urls"

TEMPLATES = (
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": (
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ),
        },
    },
)

WSGI_APPLICATION = "lerna.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

# Must be overridden in local_settings.py

DATABASES = {
    "default": {
        "ENGINE": "",
        "NAME": "",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": 0,
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "ru-RU"

TIME_ZONE = "Asia/Novosibirsk"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = "/static/"

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

AJAX_SELECT_BOOTSTRAP = False


# Authorizing
# http://djbook.ru/rel1.8/topics/auth/customizing.html

AUTH_USER_MODEL = "users.User"


TESTER = {
    "INVOKER": "",
    "EJUDGE_EXECUTE": "",
    "INVOCATION_DIRECTORY": "",
    "PROBLEM_DIRECTORY": "",
    "CHECKER_DIRECTORY": "",
}


from .local_settings import *

with contextlib.suppress(NameError):
    for key, value in PREPEND.items():
        globals()[key] = value + globals()[key]

with contextlib.suppress(NameError):
    for key, value in APPEND.items():
        globals()[key] += value
