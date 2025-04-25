"""
Django settings for the benchmark project.

This module contains the settings for the Django project, including
installed apps, middleware, database configuration, and static files.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY")

# Installed applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',  # Optional: For additional management commands
    'app',  # Custom application
]

# Template settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [Path(__file__).resolve().parent.parent / "templates"],  # Custom templates directory
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

# Middleware settings
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / "db.sqlite3",
    }
}

# Debug settings
DEBUG = True

# Allowed hosts
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Static files configuration
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]  # Custom static files directory
STATIC_ROOT = BASE_DIR / "staticfiles"  # Directory for collected static files

# Root URL configuration
ROOT_URLCONF = "config.urls"

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'